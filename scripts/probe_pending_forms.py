"""Read-only probes of forms observed in the pending-site homepage snapshots."""
import asyncio
import json
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit, parse_qsl, urlencode
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from everytune.public_http import PublicTransport

QUERIES={3:'Computerwife',5:'Bowie',6:'Metallica',7:'Beatles',8:'Beatles',14:'Skepta',15:'Beatles',16:'Ramson',17:'Shpongle',20:'Armin',21:'Astral',22:'Wiley',27:'Nas',31:'Madonna',33:'Miles',35:'Elements'}


async def main():
    directory=ROOT/'artifacts/pending-sites'
    records=json.loads((directory/'inspection.json').read_text(encoding='utf-8'))
    semaphore=asyncio.Semaphore(5)
    async with httpx.AsyncClient(transport=PublicTransport(),timeout=15,follow_redirects=False,trust_env=False,headers={'Accept-Encoding':'identity','User-Agent':'EveryTune/0.2 public search'}) as client:
        async def probe(i,query):
            record=records[i];report={'name':record['name'],'query':query,'index':i}
            try:
                async with semaphore,asyncio.timeout(40):
                    soup=BeautifulSoup((directory/f'{i}.html').read_text(encoding='utf-8'),'html.parser')
                    forms=soup.select('form')
                    form=next(f for f in forms if any(f.select_one(f'input[name="{p}"]') for p in ('s','q','story','keywords','title')))
                    field=next(p for p in ('s','q','story','keywords','title') if form.select_one(f'input[name="{p}"]'))
                    endpoint=urljoin(record.get('url'),form.get('action',''))
                    parts=urlsplit(endpoint)
                    params={**dict(parse_qsl(parts.query)),**{x['name']:x.get('value','') for x in form.select('input[type=hidden][name]')},field:query}
                    for key in list(params):
                        if key.lower() in {'sid','csrf','token'}:params.pop(key)
                    endpoint=parts._replace(query='',fragment='').geturl()
                    method=form.get('method','GET').upper()
                    r=await client.get(urljoin(endpoint,'/robots.txt'))
                    if r.status_code not in (200,404,410):raise ValueError('robots unavailable')
                    robots=RobotFileParser();robots.parse(r.text.splitlines() if r.status_code==200 else [])
                    target=endpoint+'?'+urlencode(params) if method=='GET' else endpoint
                    if not robots.can_fetch('EveryTune',target):raise ValueError('robots disallowed')
                    report.update(endpoint=endpoint,method=method,query_param=field,params={k:v for k,v in params.items() if k!=field})
                    r=await client.request(method,endpoint,**({'params':params} if method=='GET' else {'data':params}))
                    report.update(status=r.status_code,location=r.headers.get('location'))
                    if r.status_code==200:
                        (directory/f'{i}-search.html').write_text(r.text,encoding='utf-8')
                        soup=BeautifulSoup(r.text,'html.parser')
                        report['headings']=[str(a)[:450] for a in soup.select('h1,h2,h3,h4')[:10]]
                        report['links']=[str(a)[:450] for a in soup.select('a[href]') if query.lower() in a.get_text(' ',strip=True).lower()][:6]
            except Exception as error:report['error']=str(error)
            print(json.dumps(report,ensure_ascii=True),flush=True)
            return report
        results=await asyncio.gather(*(probe(i,q) for i,q in QUERIES.items()))
    (directory/'form-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':asyncio.run(main())
