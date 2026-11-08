import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from everytune.app import create_app
from everytune.engine import SearchEngine
from everytune.downloads import DownloadManager
from everytune.models import SearchRequest, Settings, SourcePage, TrackResult, rank
from everytune.sources.base import SourceError
from everytune.storage import Store

HEADERS = {'X-EveryTune': '1'}


def song(id='1', **changes):
    return TrackResult(**{'source':'fixture', 'source_id':id, 'platform':'Fixture',
        'category':'Music', 'title':'Song', 'artist':'Artist', 'kind':'track',
        'url':'https://example.org/song', **changes})


def test_recording_groups_preserve_versions_unknown_names_and_source_order():
    rows = [song('a'), song('b', source='other'), song('live', title='Song (Live)'),
        song('remix', title='Song (Remix)'), song('unknown1', artist=None),
        song('unknown2', artist=None), song('duration1', duration=180), song('duration2', duration=210)]
    found = rank(rows, SearchRequest(query='Artist', mode='source').terms())
    assert [t.source_id for t in found] == [t.source_id for t in rows]
    assert found[0].recording_group == found[1].recording_group
    assert len({t.recording_group for t in found[1:]}) == 7
    assert all(t.matched_on == 'source' for t in found)


@pytest.mark.asyncio
async def test_diagnostics_separate_names_no_audio_failure_and_timeout(tmp_path):
    store = Store(tmp_path)
    class Source:
        id='fixture'; name='Fixture'; interval=0; last_request=0; ttl=60
        def ready(self): return True
        async def search_precise(self, *args):
            return SourcePage(tracks=[song('good'), song('none'), song('failed'), song('timeout'), song('wrong', title='Other')])
    class Files:
        def register(self, track): return track.source_id
        async def confirm_audio(self, ref):
            if ref=='failed': raise SourceError('unavailable', 'Safe failure')
            if ref=='timeout': raise TimeoutError()
            return ref=='good'
        def manifest(self, ref):
            return {'options':[{'kind':'audio','delivery':'direct','format':'MP3','filename':'song.mp3'}]}
    async with httpx.AsyncClient() as client:
        engine=SearchEngine(store, client, {}, downloads=Files())
        result=await engine.search_source(Source(), SearchRequest(query='Artist - Song'), store.settings())
        assert result['diagnostics']=={'candidates':5,'name_or_version':1,'no_audio':1,
            'audio_check_failed':1,'audio_check_timeout':1,'audio_confirmed':1}
        assert result['rejected_count']==4
        assert result['tracks'][0]['audio_formats']==['MP3']
    store.close()


def test_measurements_are_bounded_private_and_survive_restart(tmp_path):
    store=Store(tmp_path)
    value={'mode':'auto','page':False,'with_audio':True,'first_audio_ms':25,
        'sources':[{'source':'fixture','status':'success','cached':True,'audio_count':1,'diagnostics':{}}]}
    for _ in range(502): store.measure('search',value)
    store.measure('download',{'source':'fixture','status':'ready'})
    store.measure('download',{'source':'fixture','status':'failed'})
    store.close(); store=Store(tmp_path)
    report=store.coverage()
    assert report['searches']==500 and report['with_audio']==500
    assert report['first_audio_ms']==25 and report['downloads']=={'ready':1,'failed':1}
    assert report['sources'][0]['attempts']==500
    assert report['sources'][0]['with_audio']==500 and report['sources'][0]['cached']==500
    assert report['sources'][0]['downloads']=={'ready':1,'failed':1}
    store.clear_coverage()
    assert store.coverage()['searches']==0
    store.close()


def test_preferences_profile_roundtrip_and_coverage_endpoint(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'results':[]})))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        original=client.get('/api/settings').json()
        assert original['download_format']=='' and original['download_pack']=='zip'
        changes={**original,'download_format':'FLAC','download_pack':'original','download_images':True}
        assert client.put('/api/settings',headers=HEADERS,json=changes).status_code==200
        assert client.get('/api/profile').json()['settings']['download_format']=='FLAC'
        assert client.put('/api/settings',headers=HEADERS,json={**changes,'download_pack':'tar'}).status_code==422
        app.state.store.measure('download',{'source':'openverse','status':'ready'})
        assert client.get('/api/coverage').json()['downloads']['ready']==1
        assert client.delete('/api/coverage').status_code==403
        assert client.delete('/api/coverage',headers=HEADERS).status_code==200
        assert client.get('/api/coverage').json()['downloads']=={}
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/settings').json()['download_pack']=='original'


def test_search_measurements_include_skipped_without_counting_catalogue(tmp_path):
    app=create_app(tmp_path,transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'results':[]})))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        result=client.post('/api/search',headers=HEADERS,json={'query':'Artist','sources':['itunes','bandcamp']}).json()
        assert result['tracks']==[] and result['sources']==[]
        assert {r['source'] for r in result['skipped']}=={'itunes','bandcamp'}
        assert client.get('/api/coverage').json()['searches']==1
        assert client.get('/api/coverage').json()['with_audio']==0


@pytest.mark.asyncio
async def test_file_check_failure_is_not_reported_as_no_audio_and_jobs_are_measured(tmp_path,monkeypatch):
    store=Store(tmp_path)
    async def no_probe(*args): return None
    monkeypatch.setattr('everytune.downloads.inspect_audio',no_probe)
    def handler(request):
        if request.url.path=='/missing.mp3':return httpx.Response(503)
        return httpx.Response(200,content=b'ID3test',headers={'Content-Type':'audio/mpeg'})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        manager=DownloadManager(client,client,store)
        try:
            ref=manager.register(song())
            manager.set_assets(ref,[{'url':'https://example.org/missing.mp3','filename':'song.mp3'}])
            with pytest.raises(SourceError):await manager.confirm_audio(ref)
            manager.set_assets(ref,[{'url':'https://example.org/song.mp3','filename':'song.mp3'}])
            job=manager.prepare(ref,[manager.manifest(ref)['options'][0]['id']],pack='original')
            await manager.tasks[job['id']]
            assert manager.job(job['id'])['status']=='ready'
            assert store.coverage()['downloads']=={'ready':1}
            assert store.coverage()['sources'][0]['downloads']=={'ready':1}
        finally:await manager.aclose()
    store.close()
