import io
import asyncio
import shutil
import wave
import zipfile

import httpx
import pytest

from everytune.audio_quality import declared_quality,inspect_audio,probe_quality
from everytune.downloads import DownloadManager,openverse_assets
from everytune.models import TrackResult
from everytune.storage import Store


def test_declared_quality_rejects_invalid_values_and_keeps_alternatives_separate():
    assert declared_quality({'bit_rate':True,'sample_rate':float('nan'),'channels':-1,'codec':'<script>'}) is None
    assert declared_quality('untrusted') is None
    assert declared_quality({'bit_rate':'320000','sample_rate':96000,'bits_per_sample':24})=={'bit_rate':320000,'sample_rate':96000,'bits_per_sample':24}
    assets=openverse_assets({'license':'by','url':'https://example.org/a.mp3','filetype':'mp3','bit_rate':320000,'sample_rate':44100,
        'alt_files':[{'url':'https://example.org/a.flac','filetype':'flac','sample_rate':96000}]},'Song')
    assert assets[0]['quality']['bit_rate']==320000
    assert assets[1]['quality']=={'sample_rate':96000}


def test_decoder_float_format_does_not_invent_mp3_bit_depth():
    result=probe_quality({'streams':[{'codec_type':'audio','codec_name':'mp3','sample_fmt':'fltp','sample_rate':'44100','channels':2,'bits_per_sample':0}]})
    assert result=={'sample_rate':44100,'channels':2,'codec':'mp3'}


@pytest.mark.asyncio
async def test_missing_probe_is_optional(tmp_path,monkeypatch):
    monkeypatch.setattr('everytune.audio_quality.shutil.which',lambda _:None)
    assert await inspect_audio(tmp_path/'not-needed','song.wav') is None


@pytest.mark.asyncio
async def test_probe_timeout_kills_child_and_restricts_input(tmp_path,monkeypatch):
    calls=[]
    class Process:
        returncode=None
        killed=False
        async def communicate(self):return b'',b''
        def kill(self):self.killed=True;self.returncode=-9
        async def wait(self):return self.returncode
    process=Process()
    async def spawn(*args,**kwargs):calls.extend(args);return process
    async def timeout(coroutine,timeout):coroutine.close();raise TimeoutError
    monkeypatch.setattr('everytune.audio_quality.shutil.which',lambda _:'ffprobe')
    monkeypatch.setattr('everytune.audio_quality.asyncio.create_subprocess_exec',spawn)
    monkeypatch.setattr('everytune.audio_quality.asyncio.wait_for',timeout)
    assert await inspect_audio(tmp_path/'artifact','song.m4a') is None
    assert process.killed
    assert calls[calls.index('-protocol_whitelist')+1]=='file'
    assert calls[calls.index('-f')+1]=='mov'
    assert calls[calls.index('-enable_drefs')+1]=='0'


@pytest.mark.asyncio
async def test_cancelling_inspection_kills_child(tmp_path,monkeypatch):
    started=asyncio.Event()
    class Process:
        returncode=None
        killed=False
        async def communicate(self):started.set();await asyncio.Event().wait()
        def kill(self):self.killed=True;self.returncode=-9
        async def wait(self):return self.returncode
    process=Process()
    async def spawn(*args,**kwargs):return process
    monkeypatch.setattr('everytune.audio_quality.shutil.which',lambda _:'ffprobe')
    monkeypatch.setattr('everytune.audio_quality.asyncio.create_subprocess_exec',spawn)
    task=asyncio.create_task(inspect_audio(tmp_path/'artifact','song.wav'))
    await started.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert process.killed


@pytest.mark.asyncio
@pytest.mark.parametrize('pack,storage_error',[('original',False),('zip',False),('zip',True)])
async def test_inspects_real_audio_and_preserves_original_and_zip_bytes(tmp_path,pack,storage_error,monkeypatch):
    if not shutil.which('ffprobe'):pytest.skip('Optional ffprobe is not installed')
    memory=io.BytesIO()
    with wave.open(memory,'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(3);wav.setframerate(96000);wav.writeframes(b'\x00'*5760)
    original=memory.getvalue()
    store=Store(tmp_path)
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,content=original,headers={'Content-Type':'audio/wav'}))) as client:
        manager=DownloadManager(client,client,store)
        try:
            if storage_error:
                def unavailable(*args,**kwargs):raise OSError('Optional inspection storage unavailable')
                monkeypatch.setattr('everytune.downloads.tempfile.TemporaryDirectory',unavailable)
            ref=manager.register(TrackResult(source='fixture',source_id='1',platform='Fixture',category='Music',title='Song',url='https://example.org/song'))
            assets=[{'url':'https://example.org/song.wav','filename':'song.wav','quality':{'sample_rate':44100}}]
            if pack=='zip':assets.append({**assets[0],'url':'https://example.org/second.wav'})
            manager.set_assets(ref,assets)
            job=manager.prepare(ref,[o['id'] for o in manager.manifest(ref)['options']],pack=pack)
            await manager.tasks[job['id']]
            ready=manager.job(job['id'])
            assert ready['status']=='ready'
            q=ready['quality_files'][0]
            assert q['declared']['sample_rate']==44100
            if storage_error:assert q['measured'] is None
            else:assert q['measured']['sample_rate']==96000 and q['measured']['bits_per_sample']==24 and q['measured']['channels']==2
            if pack=='original':assert manager.artifact(job['id']).read_bytes()==original
            else:
                with zipfile.ZipFile(manager.artifact(job['id'])) as bundle:
                    assert bundle.namelist()==['song.wav','song_2.wav']
                    assert all(bundle.read(name)==original for name in bundle.namelist())
                    assert [q['filename'] for q in ready['quality_files']]==bundle.namelist()
        finally:await manager.aclose()
    store.close()
