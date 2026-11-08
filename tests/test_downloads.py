import asyncio
import io
import json
from pathlib import Path
import zipfile

import httpx
import pytest

from everytune.downloads import DownloadManager, archive_assets, page_assets, safe_filename
from everytune.models import TrackResult
from everytune.storage import Store


def test_page_options_capture_files_packages_mirrors_and_ignore_navigation():
    html='''<a href="/song.flac">FLAC</a><a href="/album.zip">Álbum completo ZIP</a>
    <a href="https://mega.nz/file/example#key">Download MP3 320</a><a href="/sheet.pdf">Partitura</a>
    <a href="/score.mid">MIDI</a><a href="/category/rock">Rock</a><a href="javascript:alert(1)">Download</a>
    <a href="https://127.0.0.1/a.zip">ZIP</a><audio src="/stream.mp3"></audio>'''
    assets=page_assets(html,'https://example.org/post')
    assert {a['format'] for a in assets}=={'FLAC','ZIP','PDF','MID','MP3'}
    assert len(assets)==5
    assert next(a for a in assets if 'mega.nz' in a['url'])['delivery']=='external'
    assert not any('stream.mp3' in a['url'] for a in assets)


def test_archive_keeps_all_advertised_file_types_and_skips_private():
    payload={'files':[{'name':'disc/one.flac','format':'Flac','size':'123'}, {'name':'book.pdf','size':'45'}, {'name':'metadata.xml'}, {'name':'private.wav','private':'true'}]}
    files=archive_assets(payload,'item/id')
    assert len(files)==3 and files[0]['size']==123
    assert 'item%2Fid/disc/one.flac' in files[0]['url']
    assert archive_assets({**payload,'is_dark':True},'id')==[]


def test_filenames_cannot_escape_archive_or_create_windows_special_files():
    assert '/' not in safe_filename('../../disc/song.flac')
    assert '\\' not in safe_filename('..\\song.flac')
    assert safe_filename('CON.mp3').startswith('_')


def test_file_host_pages_without_download_labels_are_kept_as_external():
    assets=page_assets('<main><a href="https://rapidgator.net/file/id/album.rar.html">RG</a><a href="/tag/flac">FLAC</a></main>','https://example.org/album')
    assert len(assets)==1 and assets[0]['delivery']=='external' and assets[0]['format'] is None


def test_plain_published_links_and_static_download_buttons_without_script_execution():
    html='<article><pre>https://rapidgator.net/file/id/album.rar.html</pre><button data-url="/album.zip">Baixar álbum</button><script>var x="https://example.org/secret.flac";</script></article>'
    assets=page_assets(html,'https://example.org/post')
    assert len(assets)==2 and {a['delivery'] for a in assets}=={'direct','external'}
    assert not any('secret' in a['url'] for a in assets)


def test_primary_post_wins_over_sidebar_articles_and_unrelated_covers():
    html='<body class="single postid-42"><aside><article><a href="/unrelated.jpg">Cover</a></article></aside><div id="post-42" class="post"><a href="https://filecrypt.cc/Container/album.html">FLAC</a></div></body>'
    assets=page_assets(html,'https://example.org/album')
    assert len(assets)==1 and assets[0]['url']=='https://filecrypt.cc/Container/album.html'
    assert assets[0]['format']=='FLAC' and assets[0]['delivery']=='external'


def track():
    return TrackResult(source='fixture',source_id='1',platform='Fixture',category='Community',title='Album',url='https://example.org/album')


@pytest.mark.asyncio
async def test_download_zip_selection_bytes_duplicates_and_secret_redirect(tmp_path):
    requests=[]
    def handler(request):
        requests.append(request)
        if request.url.host=='files.example.org':
            assert 'authorization' not in request.headers
            return httpx.Response(200,content=b'FIRST',headers={'Content-Type':'audio/flac'})
        if request.url.path=='/one':
            assert request.headers['authorization']=='Bearer OWN'
            return httpx.Response(302,headers={'Location':'https://files.example.org/one.flac'})
        return httpx.Response(200,content=b'SECOND',headers={'Content-Type':'audio/flac'})
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        manager=DownloadManager(client,client,store)
        ref=manager.register(track())
        manager.set_assets(ref,[{'url':'https://example.org/one','filename':'../same.flac','headers':{'Authorization':'Bearer OWN'}}, {'url':'https://example.org/two','filename':'same.flac'}])
        options=manager.manifest(ref)['options']
        assert 'OWN' not in str(options) and not any(o.get('url') for o in options)
        job=manager.prepare(ref,[o['id'] for o in options],pack='zip')
        await manager.tasks[job['id']]
        ready=manager.job(job['id'])
        assert ready['status']=='ready'
        with zipfile.ZipFile(manager.artifact(job['id'])) as bundle:
            assert len(bundle.namelist())==2 and len(set(bundle.namelist()))==2
            assert set(bundle.read(n) for n in bundle.namelist())=={b'FIRST',b'SECOND'}
            assert all('/' not in n and '..' not in n for n in bundle.namelist())
        with pytest.raises(ValueError):manager.prepare(ref,['forged'],pack='zip')
        manager.begin_serving(job['id'])
        manager.jobs[job['id']]['updated']-=1900
        manager.cleanup()
        assert manager.artifact(job['id']).exists()
        with pytest.raises(ValueError):await manager.cancel(job['id'])
        manager.end_serving(job['id'])
        await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_transfer_refuses_redirect_to_private_address_and_html_disguised_as_audio(tmp_path):
    def handler(request):
        return httpx.Response(302,headers={'Location':'https://127.0.0.1/secret'}) if request.url.path=='/redirect' else httpx.Response(200,text='Login needed',headers={'Content-Type':'text/html'})
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        manager=DownloadManager(client,client,store)
        ref=manager.register(track())
        for path in ('redirect','login'):
            manager.set_assets(ref,[{'url':f'https://example.org/{path}','filename':'song.mp3'}])
            option=manager.manifest(ref)['options'][0]
            job=manager.prepare(ref,[option['id']],pack='original')
            await manager.tasks[job['id']]
            assert manager.job(job['id'])['status']=='failed'
        await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_audius_access_flag_alone_does_not_offer_a_file(tmp_path):
    data=json.loads((Path(__file__).parent/'fixtures/download_audius.json').read_text(encoding='utf-8'))
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={'data':data['data'][0]}))) as client:
        manager=DownloadManager(client,client,store)
        ref=manager.register(track().model_copy(update={'source':'audius','source_id':'mWB22'}))
        result=await manager.resolve(ref)
        assert result['options']==[] and result['notices']
        await manager.aclose()
    store.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('unknown_size',[False,True])
async def test_oversized_file_fails_and_removes_partial_artifact(tmp_path,unknown_size):
    from everytune.models import Settings
    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(11):yield b'x'*1024**2
    def handler(request):
        return httpx.Response(200,stream=Stream(),headers={'Content-Type':'audio/flac',**({} if unknown_size else {'Content-Length':str(11*1024**2)})})
    store=Store(tmp_path);store.save_settings(Settings(download_max_mb=10))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        manager=DownloadManager(client,client,store);ref=manager.register(track())
        manager.set_assets(ref,[{'url':'https://example.org/large','filename':'large.flac'}])
        option=manager.manifest(ref)['options'][0];job=manager.prepare(ref,[option['id']],pack='original')
        await manager.tasks[job['id']]
        assert manager.job(job['id'])['status']=='failed'
        assert not (manager.directory/job['id']).exists()
        if not unknown_size:assert manager.job(job['id'])['bytes']==0
        await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_revoking_source_invalidates_options_and_cancels_pending_transfer(tmp_path,monkeypatch):
    # Revocation cannot rely on uptime being longer than a reference's lifetime.
    monkeypatch.setattr('everytune.downloads.time.monotonic',lambda:100.0)
    class SlowStream(httpx.AsyncByteStream):
        async def __aiter__(self):
            await asyncio.Event().wait()
            yield b'never'
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,stream=SlowStream(),headers={'Content-Type':'audio/flac'}))) as client:
        manager=DownloadManager(client,client,store);ref=manager.register(track())
        manager.set_assets(ref,[{'url':'https://example.org/file','filename':'one.flac'}])
        job=manager.prepare(ref,[manager.manifest(ref)['options'][0]['id']],pack='original')
        await asyncio.sleep(0)
        await manager.invalidate({'fixture'})
        assert job['id'] not in manager.jobs and not (manager.directory/job['id']).exists()
        with pytest.raises(KeyError):manager.manifest(ref)
        await manager.aclose()
    store.close()


@pytest.mark.asyncio
async def test_head_probe_confirms_attachment_without_reading_media(tmp_path):
    class NoBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError('HEAD must not read media')
            yield b''
    def handler(request):
        assert request.method=='HEAD'
        return httpx.Response(200,headers={'Content-Type':'audio/flac','Content-Length':'123','Content-Disposition':'attachment; filename="original.flac"'},stream=NoBody())
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        manager=DownloadManager(client,client,store);ref=manager.register(track())
        manager.set_assets(ref,[{'url':'https://example.org/download.php','filename':'pending.flac','delivery':'external'}])
        id=manager.manifest(ref)['options'][0]['id']
        data=await manager.probe(ref,id)
        assert data['options'][0]['id']==id and data['options'][0]['delivery']=='direct'
        assert data['options'][0]['format']=='FLAC' and data['options'][0]['size']==123
        assert data['options'][0]['open_url'] is None
        await manager.aclose()
    store.close()


def test_manual_inspection_rejects_foreign_private_domains_and_unknown_source(tmp_path):
    from fastapi.testclient import TestClient
    from everytune.app import create_app
    app=create_app(tmp_path)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        for source,url in [('archive','https://archive.org.evil.example/details/item'),('custom_ocremix','https://127.0.0.1/file'),('unknown','https://example.org/')]:
            assert client.post('/api/downloads/inspect',headers={'X-EveryTune':'1'},json={'source':source,'url':url}).status_code==422


@pytest.mark.asyncio
async def test_metadata_transport_stays_separate_from_binary_transfers(monkeypatch):
    import socket
    from everytune.public_http import PublicTransport
    from everytune.sources.base import SourceError
    async def resolve(*args,**kwargs):return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))]
    monkeypatch.setattr(asyncio.get_running_loop(),'getaddrinfo',resolve)
    for metadata in (True,False):
        transport=PublicTransport(metadata=metadata)
        await transport.transport.aclose()
        transport.transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'AUDIO',headers={'Content-Type':'audio/mpeg'}))
        async with httpx.AsyncClient(transport=transport) as client:
            if metadata:
                with pytest.raises(SourceError):await client.get('https://example.org/file.mp3')
            else:assert (await client.get('https://example.org/file.mp3')).content==b'AUDIO'


def test_api_issues_references_and_serves_only_selected_zip_files(tmp_path):
    import time
    from fastapi.testclient import TestClient
    from everytune.app import create_app
    def handler(request):
        if request.url.path=='/advancedsearch.php':return httpx.Response(200,json={'response':{'numFound':1,'docs':[{'identifier':'fixture','title':'Album'}]}})
        if request.url.path=='/metadata/fixture':return httpx.Response(200,json={'files':[{'name':'one.flac'},{'name':'two.flac'},{'name':'not-selected.flac'},{'name':'metadata.xml'}]})
        return httpx.Response(200,content=request.url.path.rsplit('/',1)[-1].encode(),headers={'Content-Type':'audio/flac'})
    app=create_app(tmp_path,transport=httpx.MockTransport(handler))
    headers={'X-EveryTune':'1'}
    with TestClient(app,base_url='http://127.0.0.1') as client:
        manager=app.state.downloads
        manager.metadata_client=manager.transfer_client=app.state.engine.sources['archive'].client
        result=client.post('/api/search',headers=headers,json={'query':'Album','sources':['archive'],'mode':'source'}).json()
        ref=result['tracks'][0]['download_ref']
        manifest=client.post('/api/downloads/resolve/'+ref,headers=headers).json()
        ids=[o['id'] for o in manifest['options'][:2]]
        assert client.post('/api/downloads/prepare',headers=headers,json={'ref':ref,'option_ids':ids,'pack':'zip','url':'https://localhost/'}).status_code==422
        response=client.post('/api/downloads/prepare',headers=headers,json={'ref':ref,'option_ids':ids,'pack':'zip'})
        assert response.status_code==200;job=response.json()
        for _ in range(100):
            current=client.get('/api/downloads/jobs').json()[0]
            if current['status'] not in {'queued','running'}:break
            time.sleep(.01)
        assert current['status']=='ready'
        file=client.get('/api/downloads/files/'+job['id'])
        assert file.status_code==200 and 'attachment' in file.headers['content-disposition']
        with zipfile.ZipFile(io.BytesIO(file.content)) as bundle:assert bundle.namelist()==['one.flac','two.flac']
        assert client.delete('/api/downloads/jobs/'+job['id'],headers=headers).status_code==200
        assert client.get('/api/downloads/files/'+job['id']).status_code==404
