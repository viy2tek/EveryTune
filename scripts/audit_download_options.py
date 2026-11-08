"""Read offered file options from known source result pages; never transfer media."""
import asyncio
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import httpx

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from everytune.app import source_presets
from everytune.downloads import DownloadManager
from everytune.engine import SearchEngine
from everytune.models import TrackResult
from everytune.public_http import PublicTransport
from everytune.storage import Store


async def main():
    output=ROOT/'docs/download-options-audit.json'
    previous={r['source']:r for r in json.loads(output.read_text(encoding='utf-8'))['sources']} if '--retry-missing' in sys.argv and output.exists() else {}
    targets={}
    for filename in ('free-connectors-live.json','federated-live.json'):
        for row in json.loads((ROOT/'docs'/filename).read_text(encoding='utf-8')):
            if row.get('examples'):
                item=row['examples'][0]
                targets[row['id']]={'source':row['id'],'source_id':hashlib.sha256(item['url'].encode()).hexdigest()[:24],'platform':row['name'],'category':'Comunidade','title':item['title'],'url':item['url']}
    targets['archive']={'source':'archive','source_id':'sam-torres-still','platform':'Internet Archive','category':'Acervos','title':'Sam Torres - Still','url':'https://archive.org/details/sam-torres-still'}
    semaphore=asyncio.Semaphore(5)
    with tempfile.TemporaryDirectory(prefix='everytune-download-audit-') as directory:
        store=Store(Path(directory));store.initialize_sources(source_presets())
        async with httpx.AsyncClient(transport=PublicTransport(),timeout=15,trust_env=False,follow_redirects=False,headers={'User-Agent':'EveryTune/0.4 public file metadata audit','Accept-Encoding':'identity'}) as client:
            manager=DownloadManager(client,client,store)
            manager.engine=SearchEngine(store,client,{},client,manager)
            async def inspect(value):
                row={'source':value['source'],'name':value['platform'],'page_url':value['url']}
                try:
                    async with semaphore,asyncio.timeout(45):
                        data=await manager.resolve(manager.register(TrackResult(**value)))
                    row.update(status='options_found' if data['options'] else 'no_options',direct=sum(o['delivery']=='direct' for o in data['options']),external=sum(o['delivery']=='external' for o in data['options']),kinds=dict(Counter(o['kind'] for o in data['options'])),formats=sorted({o['format'] for o in data['options'] if o['format']}),examples=[{k:o[k] for k in ('label','filename','format','kind','delivery')} for o in data['options'][:4]],notices=data['notices'])
                except Exception as error:row.update(status='unavailable',reason=getattr(error,'message',type(error).__name__))
                print(json.dumps(row,ensure_ascii=True),flush=True)
                return row
            checked=await asyncio.gather(*(inspect(v) for id,v in targets.items() if previous.get(id,{}).get('status')!='options_found'))
            combined={**previous,**{r['source']:r for r in checked}}
            results=[combined[id] for id in targets if id in combined]
            await manager.aclose()
        store.close()
    output.write_text(json.dumps({'scope':'One known result per available configured website; metadata only, no file transfers','sources':results},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':asyncio.run(main())
