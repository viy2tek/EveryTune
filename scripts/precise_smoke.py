"""Live regression check for artist/title verification, using a temporary database."""
import asyncio
import json
from pathlib import Path
import tempfile
import sys

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from everytune.engine import SearchEngine
from everytune.models import SearchRequest, normalize
from everytune.storage import Store


async def main():
    reports=[]
    with tempfile.TemporaryDirectory(prefix="everytune-precise-") as directory:
        store=Store(Path(directory))
        try:
            async with httpx.AsyncClient(timeout=12,follow_redirects=False,headers={"User-Agent":"EveryTune/0.1 (local music discovery; https://fmhy.net/audio)"}) as client:
                engine=SearchEngine(store,client,{})
                for query in ("Soft Pillow Kisses - Stolen Flowers","Daft Punk - Get Lucky"):
                    request=SearchRequest(query=query,limit=15)
                    events=[event async for event in engine.events(request)]
                    result=events[-1]
                    terms=request.terms()
                    for track in result['tracks']:
                        assert normalize(track['title'])==normalize(terms.title)
                        assert normalize(terms.artist) in {normalize(name) for name in (track.get('artist_names') or [])+[track.get('artist') or '']}
                        assert track['matched_on']=='artist_title'
                    if query.startswith('Daft Punk'):
                        assert result['tracks'],result['sources']
                    reports.append(result)
        finally:store.close()
    path=Path(__file__).resolve().parent.parent/'docs'/'precise-smoke.json'
    path.write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    for report in reports:
        print(json.dumps({'query':report['query'],'matches':len(report['tracks']),'sources':{s['source']:{'status':s['status'],'rejected':s['rejected_count']} for s in report['sources']},'tracks':[{'title':t['title'],'artist':t['artist'],'source':t['source']} for t in report['tracks']]},ensure_ascii=True))


if __name__=='__main__':asyncio.run(main())
