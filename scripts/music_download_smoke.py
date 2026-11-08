"""Live search and one openly licensed audio transfer, with isolated app data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--executable',type=Path)
parser.add_argument('--coverage',action='store_true',help='Compare the three editable starter queries across six installed sources without transferring their media')
args=parser.parse_args()
report={'executable':bool(args.executable),'queries':[]}
with tempfile.TemporaryDirectory(prefix='everytune-audio-live-') as directory:
    command=[str(args.executable.resolve())] if args.executable else [sys.executable,'-m','everytune']
    process=subprocess.Popen(command+['--port','0','--no-browser'],cwd=ROOT,
        env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    lines=queue.Queue()
    def drain():
        for line in process.stdout:lines.put(line)
    threading.Thread(target=drain,daemon=True).start()
    base=None
    def api(path,body=None,method=None,binary=False):
        request=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type':'application/json','X-EveryTune':'1'},method=method)
        with urllib.request.urlopen(request,timeout=90) as response:
            return response.read() if binary else json.load(response)
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Application exited')
            try:line=lines.get(timeout=.2)
            except queue.Empty:continue
            match=re.search(r'http://127\.0\.0\.1:\d+',line)
            if match:base=match.group();break
        assert base,'No startup URL'
        for _ in range(100):
            try:api('/api/health');break
            except OSError:time.sleep(.1)
        shortcuts=api('/api/search',{'query':'Song','sources':['bandcamp']})
        assert not shortcuts['tracks'] and not shortcuts['external']
        found=api('/api/search',{'query':'xxxtentacion','mode':'auto','exclude_covers':True,'sources':['itunes','openverse'],'limit':10})
        assert all(t['recording_type']!='cover' for t in found['tracks'])
        assert all(t['artist'] and ('xxxtentacion' in [n.casefold() for n in (t.get('artist_names') or [])] or t['artist'].casefold()=='xxxtentacion') for t in found['tracks'])
        report['queries'].append({'query':'xxxtentacion','sources':found['sources'],'results':[{
            k:t.get(k) for k in ('source','title','artist','downloadable','file_access')} for t in found['tracks']]})
        query='Magic Juand - Rockstars (Instrumental) [Produced by Magic Juand]'
        found=api('/api/search',{'query':query,'mode':'auto','sources':['openverse'],'limit':5})
        assert found['tracks'],found['sources']
        track=next(t for t in found['tracks'] if t['source']=='openverse')
        assert track['audio_available'] is True
        manifest=api('/api/downloads/resolve/'+track['download_ref'],{},method='POST')
        options=[o for o in manifest['options'] if o['kind']=='audio' and o['delivery']=='direct']
        assert options,manifest
        job=api('/api/downloads/prepare',{'ref':manifest['ref'],'option_ids':[options[0]['id']],'pack':'original'})
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            job=next(j for j in api('/api/downloads/jobs') if j['id']==job['id'])
            if job['status'] not in {'queued','running'}:break
            time.sleep(.25)
        assert job['status']=='ready',job
        if shutil.which('ffprobe'):
            quality=job['quality_files'][0]['measured']
            assert quality and quality['codec']=='mp3' and quality.get('sample_rate',0)>0,job
            report['file_quality']=quality
        audio=api('/api/downloads/files/'+job['id'],binary=True)
        assert len(audio)==job['bytes'] and len(audio)>1000
        assert audio.startswith(b'ID3') or audio[0]==255,'Unexpected MP3 header'
        report['audio_download']={'query':query,'source':track['source'],'title':track['title'],'artist':track['artist'],
            'license':manifest['license'],'format':options[0]['format'],'filename':job['filename'],
            'bytes':len(audio),'sha256':hashlib.sha256(audio).hexdigest(),'status':job['status']}
        if args.coverage:
            report['coverage_sample']=[]
            for term in ['xxxtentacion','Soft Pillow Kisses - Stolen Flowers',query]:
                result=api('/api/search',{'query':term,'mode':'auto','require_audio':True,
                    'sources':['archive','openverse','audius','commons','jamendo','soundcloud'],'limit':5})
                report['coverage_sample'].append({'query':term,'audio_origins':len(result['tracks']),
                    'first_audio_ms':result['first_audio_ms'],'sources':result['sources']})
        coverage=api('/api/coverage')
        assert coverage['searches']>=3 and coverage['with_audio']>=1 and coverage['downloads'].get('ready')==1,coverage
        report['coverage']=coverage
        print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        (ROOT/'artifacts/music-download-live.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        if base:
            try:api('/api/shutdown',{},method='POST');process.wait(timeout=10)
            except Exception:process.terminate()
        else:process.terminate()
