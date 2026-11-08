import httpx
import pytest

from everytune.downloads import DownloadManager, openverse_assets
from everytune.sources.openverse import Openverse, offers_file
from everytune.storage import Store
from everytune.models import TrackResult


ITEM = {'id':'fixture-audio','title':'Rockstars','creator':'Magic Juand',
    'foreign_landing_url':'https://www.jamendo.com/track/1501817',
    'url':'https://media.example.org/?trackid=1501817&format=mp32',
    'filetype':'mp32','filesize':123,'license':'by-nd','license_url':'https://creativecommons.org/licenses/by-nd/3.0/'}


def test_openverse_preserves_real_file_formats_and_alternatives():
    payload={**ITEM,'alt_files':[{'url':'https://example.org/file.flac','filetype':'flac','filesize':456},
        {'url':'https://127.0.0.1/private.mp3','filetype':'mp3'},None]}
    assets=openverse_assets(payload,'Rockstars')
    assert len(assets)==2
    assert assets[0]['filename']=='Rockstars.mp3' and assets[0]['format']=='MP3'
    assert assets[1]['filename']=='Rockstars.flac' and assets[1]['size']==456
    assert offers_file(payload)
    assert not offers_file({**ITEM,'url':'http://example.org/file.mp3'})
    assert not offers_file({**ITEM,'url':'https://127.0.0.1/file.mp3'})
    assert openverse_assets({**ITEM,'license':'unknown'},'Rockstars')==[]


@pytest.mark.asyncio
async def test_openverse_search_resolve_prepare_and_serve_original_bytes(tmp_path):
    calls=[]
    audio=b'ID3-test-audio-data'
    def handler(request):
        calls.append(str(request.url))
        if request.url.path=='/v1/audio/':
            return httpx.Response(200,json={'results':[ITEM],'page_count':1})
        if request.url.path=='/v1/audio/fixture-audio/':
            return httpx.Response(200,json=ITEM)
        if request.url.host=='media.example.org':
            return httpx.Response(200,content=audio,headers={'Content-Type':'audio/mpeg'})
        raise AssertionError('Must not scrape Jamendo landing page: '+str(request.url))
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        source=Openverse(client,{})
        track=(await source.search('Magic Juand')).tracks[0]
        assert track.downloadable is True
        manager=DownloadManager(client,client,store)
        try:
            ref=manager.register(track)
            manifest=await manager.resolve(ref)
            assert len(manifest['options'])==1 and manifest['options'][0]['format']=='MP3'
            job=manager.prepare(ref,[manifest['options'][0]['id']],pack='original')
            await manager.tasks[job['id']]
            assert manager.job(job['id'])['status']=='ready'
            assert manager.artifact(job['id']).read_bytes()==audio
            assert not any('www.jamendo.com' in url for url in calls)
        finally:
            await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_openverse_rechecks_license_and_identity_before_preparation(tmp_path):
    payload={**ITEM,'license':'unknown'}
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=payload))) as client:
        source=Openverse(client,{})
        manager=DownloadManager(client,client,store)
        ref=manager.register(source.track(ITEM['id'],ITEM['title'],ITEM['foreign_landing_url']))
        try:
            assert (await manager.resolve(ref))['options']==[]
            payload['id']='another-record'
            with pytest.raises(ValueError,match='outro registro'):
                await manager.resolve(ref)
        finally:
            await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_catalogue_does_not_offer_a_download_action(tmp_path):
    store=Store(tmp_path)
    async with httpx.AsyncClient() as client:
        manager=DownloadManager(client,client,store)
        try:
            track=TrackResult(source='itunes',source_id='123',platform='iTunes',category='Music',title='Song',url='https://music.apple.com/song')
            assert manager.register(track) is None
            assert track.file_access=='catalogue' and not manager.refs
        finally:
            await manager.aclose()
    store.close()
