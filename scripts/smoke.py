"""Real process, static assets, search and graceful shutdown. No mock results."""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--executable", type=Path)
parser.add_argument("--live", action="store_true")
parser.add_argument("--output", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
command = [str(args.executable.resolve())] if args.executable else [sys.executable, "-m", "everytune"]
with tempfile.TemporaryDirectory(prefix="everytune-smoke-") as directory:
    process = subprocess.Popen(command+["--port", "0", "--no-browser"], cwd=root, env={**os.environ,"EVERYTUNE_DATA_DIR":directory,"PYTHONIOENCODING":"utf-8"}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    lines = queue.Queue()
    def read_output():
        for line in process.stdout: lines.put(line)
    threading.Thread(target=read_output,daemon=True).start()
    base = None
    report = {"executable":bool(args.executable),"checks":[],"queries":[]}
    try:
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if process.poll() is not None: raise RuntimeError(f"Launcher exited: {process.returncode}")
            try: line=lines.get(timeout=.2)
            except queue.Empty: continue
            match=re.search(r"http://127\.0\.0\.1:\d+",line)
            if match: base=match.group(); break
        assert base, "Launcher did not report a local URL"
        for _ in range(100):
            try:
                with urllib.request.urlopen(base+"/api/health",timeout=1) as response: assert response.status==200
                break
            except OSError: time.sleep(.1)
        else: raise AssertionError("Server never became ready")
        for path in ("/", "/api/health", "/api/profile", "/api/custom-sources", "/api/sources", "/api/source-audit", "/api/downloads/jobs", "/static/app.js", "/static/preferences.js", "/static/downloads.js", "/static/style.css", "/static/expansion.css", "/static/downloads.css", "/static/icon.svg", "/static/licenses.html", "/openapi.json"):
            with urllib.request.urlopen(base+path,timeout=3) as response:
                assert response.status==200
                payload=response.read()
                assert len(payload)>0
                if path=='/static/licenses.html':assert b'MIT License' in payload and b'Python' in payload
                if path=="/api/source-audit":
                    audit=json.loads(payload)
                    assert audit["complete"] and audit["total"]==124, audit
                if path=="/api/custom-sources":
                    definitions=json.loads(payload)
                    assert len(definitions)>=65
                    assert any(s['id']=='custom_certifiedmixtapez' and s['method']=='POST' and s['request_encoding']=='json' for s in definitions)
                if path=="/api/sources":
                    sources=json.loads(payload)
                    assert {'spotify','applemusic','soundcloud'} <= {s['id'] for s in sources if s['provider_group']=='streaming'}
            report["checks"].append(path)
        if args.live:
            for query in ("Daft Punk - Get Lucky", "Rick Astley - Never Gonna Give You Up", "Soft Pillow Kisses - Stolen Flowers"):
                request=urllib.request.Request(base+"/api/search",data=json.dumps({"query":query,"sources":["itunes","musicbrainz"],"limit":3}).encode(),headers={"Content-Type":"application/json","X-EveryTune":"1"})
                with urllib.request.urlopen(request,timeout=90) as response: data=json.load(response)
                summary={"query":query,"tracks":len(data["tracks"]),"sources":data["sources"],"examples":[{"source":t["source"],"title":t["title"],"url":t["url"]} for t in data["tracks"][:8]]}
                report["queries"].append(summary)
                if query.startswith("Soft Pillow Kisses"):
                    assert data["tracks"]==[], summary
                else:
                    assert len({t["source"] for t in data["tracks"]})>=2, summary
            request=urllib.request.Request(base+"/api/search",data=json.dumps({"query":"Gucci","mode":"source","sources":["custom_certifiedmixtapez"],"limit":3}).encode(),headers={"Content-Type":"application/json","X-EveryTune":"1"})
            with urllib.request.urlopen(request,timeout=45) as response: data=json.load(response)
            assert data['tracks'] and all(t['matched_on']=='source' for t in data['tracks']),data['sources']
            report['queries'].append({'query':'Gucci — Resultados da fonte','tracks':len(data['tracks']),'sources':data['sources'],'examples':[{'title':t['title'],'url':t['url']} for t in data['tracks']]})
            request=urllib.request.Request(base+'/api/downloads/inspect',data=json.dumps({'source':'archive','url':'https://archive.org/details/sam-torres-still'}).encode(),headers={'Content-Type':'application/json','X-EveryTune':'1'})
            with urllib.request.urlopen(request,timeout=60) as response: manifest=json.load(response)
            chosen=[o['id'] for o in manifest['options'] if o['filename'] in {'sam-torres-still_files.xml','sam-torres-still_meta.xml'}]
            assert len(chosen)==2
            request=urllib.request.Request(base+'/api/downloads/prepare',data=json.dumps({'ref':manifest['ref'],'option_ids':chosen,'pack':'zip'}).encode(),headers={'Content-Type':'application/json','X-EveryTune':'1'})
            with urllib.request.urlopen(request,timeout=5) as response: job=json.load(response)
            for _ in range(120):
                with urllib.request.urlopen(base+'/api/downloads/jobs',timeout=3) as response: jobs=json.load(response)
                current=next(j for j in jobs if j['id']==job['id'])
                if current['status'] not in {'queued','running'}:break
                time.sleep(.5)
            assert current['status']=='ready',current
            with urllib.request.urlopen(base+'/api/downloads/files/'+job['id'],timeout=5) as response: bundle=response.read()
            import io,zipfile
            with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
                assert set(archive.namelist())=={'sam-torres-still_files.xml','sam-torres-still_meta.xml'}
            report['checks'].append('real_selected_metadata_zip_no_music')
        request=urllib.request.Request(base+"/api/shutdown",data=b"",headers={"X-EveryTune":"1"})
        with urllib.request.urlopen(request,timeout=3) as response: assert response.status==200
        assert process.wait(timeout=15)==0
        report["checks"].append("graceful_shutdown")
    finally:
        if process.poll() is None:
            process.terminate(); process.wait(timeout=10)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"executable":report["executable"],"checks":report["checks"],"queries":[{"query":q["query"],"tracks":q["tracks"],"sources":{s["source"]:s["status"] for s in q["sources"]}} for q in report["queries"]]},ensure_ascii=True,indent=2))
