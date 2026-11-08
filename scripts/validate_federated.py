"""Validate candidate connectors with the application's actual bounded transport."""
import asyncio
import json
from pathlib import Path
import sys

import httpx

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from everytune.models import SearchRequest
from everytune.public_http import PublicTransport
from everytune.source_config import SourceDefinition
from everytune.sources.custom import CustomSource


async def main():
    evidence=ROOT/'docs/pending-site-evidence'
    queries={}
    for p in evidence.glob('*-result.json'):
        r=json.loads(p.read_text(encoding='utf-8'))
        if r.get('feed_endpoint'):queries[r['feed_endpoint']]=r['feed_query']
    for r in json.loads((ROOT/'artifacts/pending-sites/form-results.json').read_text(encoding='utf-8')):
        if r.get('endpoint'):queries[r['endpoint']]=r['query']
    queries.update({'https://ccmixter.org/search':'love','https://canna.to/suche':'Abba','https://canna-power.to/suche':'Abba','https://www.midicities.com/geocities-search':'titanic','https://rapload.org/':'Nas','https://gabber.od.ua/tt':'Angerfist','https://globaldjmix.com/search-result':'Solomun','https://www.systemsofromance.com/blog/':'coldwave','https://classical-music-download.com/':'Bach','https://www.certifiedmixtapez.com/Main/GetSearchResults':'Gucci','https://we-need-match.ru/search/':'Metallica'})
    candidates=[]
    for name in ('pending-research-presets.json','pending-root-presets.json'):
        candidates.extend(json.loads((ROOT/'docs'/name).read_text(encoding='utf-8')))
    installed=ROOT/'everytune/data/federated_presets.json'
    if installed.exists():
        candidates=json.loads(installed.read_text(encoding='utf-8'))
    semaphore=asyncio.Semaphore(5)
    async with httpx.AsyncClient(transport=PublicTransport(),timeout=15,follow_redirects=False,trust_env=False,headers={'User-Agent':'EveryTune/0.2 public catalogue search','Accept-Encoding':'identity'}) as client:
        async def check(value):
            config=SourceDefinition.model_validate(value)
            query=queries.get(config.endpoint,'Beatles')
            report={'id':config.id,'name':config.name,'endpoint':config.endpoint,'query':query}
            try:
                async with semaphore,asyncio.timeout(95):
                    source=CustomSource(client,{},config)
                    page=await source.search_precise(SearchRequest(query=query,mode='source').terms(),5,None)
                    report.update(matches=len(page.tracks),examples=[{'title':t.title,'url':str(t.url)} for t in page.tracks[:3]],next_cursor=page.next_cursor)
                    if source.interval>30:
                        await asyncio.sleep(source.interval+0.1)
                    negative=await source.search_precise(SearchRequest(query='EveryTuneImpossibleQuery78147814',mode='source').terms(),5,None)
                    report['negative_count']=len(negative.tracks)
                    report['status']='success' if page.tracks and not negative.tracks else 'needs_review'
            except Exception as error:report.update(status='unavailable',error=getattr(error,'message',type(error).__name__))
            print(json.dumps(report,ensure_ascii=True),flush=True)
            return report
        reports=await asyncio.gather(*(check(c) for c in candidates))
    (ROOT/'docs/federated-live.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':asyncio.run(main())
