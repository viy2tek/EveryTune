"""Live read-only checks of public website presets using the production transport."""
import asyncio
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import httpx
from everytune.app import source_presets
from everytune.models import SearchRequest, rank
from everytune.public_http import PublicTransport
from everytune.sources.custom import CustomSource


async def main():
    audit=json.loads((ROOT/'docs/free-websites-audit.json').read_text(encoding='utf-8'))
    queries={r['preset_id']:r['searches'][-1]['query'] for r in audit['sources'] if r.get('preset_id')}
    queries.update(custom_ucsb_cylinders='Kathleen Parlow',custom_vgmrips='Koji Kondo',custom_ocremix='Avitron')
    queries['custom_web_c08f92175f']='Tiesto'
    semaphore=asyncio.Semaphore(4)
    async with httpx.AsyncClient(transport=PublicTransport(),timeout=12,follow_redirects=False,trust_env=False,headers={'User-Agent':'EveryTune/0.1 (public catalogue search)','Accept-Encoding':'identity'}) as client:
        async def check(definition):
            query=queries.get(definition.id,'Beatles')
            report={'id':definition.id,'name':definition.name,'query':query,'endpoint':definition.endpoint}
            try:
                async with semaphore:
                    async with asyncio.timeout(25):
                        page=await CustomSource(client,{},definition).search(query,limit=20)
                terms=SearchRequest(query=query,mode='credits' if definition.id in {'custom_ucsb_cylinders','custom_vgmrips','custom_ocremix'} else 'auto').terms()
                matches=rank(page.tracks,terms)
                report.update(status='success' if matches else 'no_match',candidates=len(page.tracks),matches=len(matches),examples=[{'title':t.title,'url':str(t.url),'matched_on':t.matched_on} for t in matches[:2]],notices=page.notices)
            except Exception as error:
                report.update(status='unavailable',reason=getattr(error,'message',type(error).__name__))
            print(json.dumps(report,ensure_ascii=True),flush=True)
            return report
        reports=await asyncio.gather(*(check(d) for d in source_presets() if d.format!='external'))
    (ROOT/'docs/free-connectors-live.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    assert any(r['status']=='success' for r in reports),'No public website connector could be validated'


if __name__=='__main__':asyncio.run(main())
