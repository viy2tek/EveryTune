"""Read public search forms for the second half of the unresolved website audit."""
import asyncio
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.audit_sources import Auditor


async def main():
    records = json.loads((ROOT/'docs/free-websites-audit.json').read_text(encoding='utf-8'))['sources']
    records = [r for r in records if r['outcome'] in {'no_public_get_search_observed','search_not_verified'}][35:]
    directory = ROOT/'artifacts/pending-sites'
    directory.mkdir(exist_ok=True)
    auditor = Auditor(6, 15)
    async def inspect(index, record):
        try:
            async with asyncio.timeout(40):
                page = await auditor.fetch(record['url'], 1_000_000)
            body = page.pop('body','')
            (directory/f'{index}.html').write_text(body,encoding='utf-8')
            soup = BeautifulSoup(body,'html.parser')
            result = {'name':record['name'],'url':record['url'],'file':f'{index}.html',**page,
                'forms':[str(f)[:6000] for f in soup.select('form')],
                'scripts':[s.get('src') or s.get_text()[:2000] for s in soup.select('script') if s.get('src') or 'search' in s.get_text().lower()],
                'search_links':[a.get('href') for a in soup.select('a[href]') if 'search' in a.get('href','').lower()][:12]}
        except Exception as error:
            result = {'name':record['name'],'url':record['url'],'error':type(error).__name__}
        print(json.dumps(result,ensure_ascii=True),flush=True)
        return result
    results = await asyncio.gather(*(inspect(i,r) for i,r in enumerate(records)))
    (directory/'inspection.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    asyncio.run(main())
