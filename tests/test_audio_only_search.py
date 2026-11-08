import httpx
import pytest
from fastapi.testclient import TestClient

from everytune.app import create_app
from everytune.downloads import DownloadManager
from everytune.models import TrackResult
from everytune.storage import Store

HEADERS={'X-EveryTune':'1'}


def test_search_counts_only_verified_audio_and_manifest_only_media(tmp_path):
    calls=[]
    class NoBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError('Availability must not read media')
            yield b''
    def handler(request):
        calls.append((request.method,request.url.path))
        if request.url.path=='/advancedsearch.php':
            return httpx.Response(200,json={'response':{'numFound':4,'docs':[{'identifier':i,'title':'Song'} for i in ['good','image','broken','html']]}})
        if request.url.path.startswith('/metadata/'):
            id=request.url.path.rsplit('/',1)[-1]
            files=[{'name':'cover.jpg'},{'name':'metadata.xml'},{'name':'book.pdf'},{'name':'album.zip'},{'name':'video.mp4'}]
            if id!='image':files.insert(0,{'name':'song.flac'})
            return httpx.Response(200,json={'files':files})
        if '/broken/' in request.url.path:return httpx.Response(404)
        mime='text/html' if '/html/' in request.url.path else 'audio/flac'
        if request.method=='HEAD':return httpx.Response(200,headers={'Content-Type':mime,'Content-Length':'3'},stream=NoBody())
        raise AssertionError('Search must not GET media')
    app=create_app(tmp_path,transport=httpx.MockTransport(handler))
    with TestClient(app,base_url='http://127.0.0.1') as client:
        manager=app.state.downloads
        manager.metadata_client=manager.transfer_client=app.state.engine.sources['archive'].client
        body={'query':'Song','mode':'source','sources':['archive']}
        for cached in [False,True]:
            result=client.post('/api/search',headers=HEADERS,json=body).json()
            assert len(result['tracks'])==1
            track=result['tracks'][0]
            assert track['source_id']=='good' and track['audio_available'] is True
            assert result['sources'][0]['rejected_count']==3
            assert result['sources'][0]['cached']==cached
            ref=track['download_ref']
            options=manager.manifest(ref)['options']
            assert {o['filename'] for o in options}=={'song.flac','cover.jpg'}
            forbidden=next(id for id,a in manager.record(ref)['assets'].items() if a['filename']=='book.pdf')
            response=client.post('/api/downloads/prepare',headers=HEADERS,json={'ref':ref,'option_ids':[forbidden],'pack':'original'})
            assert response.status_code==422
        assert any(method=='HEAD' and '/download/' in path for method,path in calls)
        assert not any(method=='GET' and '/download/' in path for method,path in calls)
        catalogue=client.post('/api/search',headers=HEADERS,json={'query':'Song','sources':['itunes']}).json()
        assert catalogue['tracks']==[] and catalogue['sources']==[]
        shortcuts=client.post('/api/search',headers=HEADERS,json={'query':'Song','sources':['bandcamp']}).json()
        assert shortcuts['tracks']==[] and shortcuts['external']==[]


@pytest.mark.asyncio
@pytest.mark.parametrize('mime,disposition',[('application/pdf',''),('audio/flac','attachment; filename="not-audio.exe"')])
async def test_transfer_rejects_other_mime_or_filename(tmp_path,mime,disposition):
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'bytes',headers={'Content-Type':mime,'Content-Disposition':disposition}))) as client:
        manager=DownloadManager(client,client,store)
        try:
            ref=manager.register(TrackResult(source='fixture',source_id='1',platform='Fixture',category='Music',title='Song',url='https://example.org/song'))
            manager.set_assets(ref,[{'url':'https://example.org/song.flac','filename':'song.flac'}])
            job=manager.prepare(ref,[manager.manifest(ref)['options'][0]['id']],pack='original')
            await manager.tasks[job['id']]
            assert manager.job(job['id'])['status']=='failed'
            assert not (manager.directory/job['id']).exists()
        finally:await manager.aclose()
    store.close()
