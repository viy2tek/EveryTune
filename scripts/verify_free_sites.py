"""Inspect the user-selected FMHY website sections and validate public HTML search mappings."""
import asyncio
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import httpx

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from scripts.audit_sources import Auditor, PageParser, now
from everytune.source_config import SourceDefinition

SECTIONS={'download-sites':'Download Sites','genre-specific-ripping':'Genre Specific Ripping'}
SKIP_HOSTS={'rentry.co','discord.gg','github.com','gitlab.com','cse.google.com','t.me','fmhy.net'}


def targets_from_html(html):
    soup=BeautifulSoup(html,'html.parser')
    targets={}
    for id,label in SECTIONS.items():
        heading=soup.find(id=id)
        if heading is None:raise ValueError('FMHY section missing: '+id)
        for sibling in heading.next_siblings:
            if getattr(sibling,'name',None) in {'h1','h2','h3'}:break
            if not getattr(sibling,'find_all',None):continue
            for anchor in sibling.find_all('a',href=True):
                url=anchor['href']
                if not url.startswith(('https://','http://')):continue
                context = anchor.find_parent('li').get_text(' ',strip=True).casefold() if anchor.find_parent('li') else ''
                hint = next((genre for genre in ('hip hop','metal','rock','electronic','jazz','classical','pop') if genre in context),'other')
                record=targets.setdefault(url,{'url':url,'name':anchor.get_text(' ',strip=True),'sections':[],'genre_hint':hint})
                if label not in record['sections']:record['sections'].append(label)
    return list(targets.values())


def mapping_for_html(html, query=None):
    soup=BeautifulSoup(html,'html.parser')
    candidates=[('article','h2 a'),('article','h3 a'),('.post','h3.post-title a'),('.post','h2 a'),('.post','h3 a'),('.post-outer','h3 a'),('.news-item','h2 a'),('.shortstory','h2 a'),('.short','h2 a'),('.block_story','h2 a'),('.entry-title','a'),('.post-title','a'),('.story-title','a'),('.post_title','a'),('.shortstory','.title a'),('.news','.title a'),('.short-item','.title a'),('.news-title','a'),('.title-news','a'),('h2 a[href]',''),('h3 a[href]',''),('#dle-content a[href]',''),('main a[href]','')]
    for records,title in candidates:
        rows=soup.select(records)
        anchors=[row.select_one(title) if title else row for row in rows]
        valid=[a for a in anchors if a and a.get('href') and not any(part in a['href'].lower() for part in ('/category/','/tag/','?','#','.mp3','.flac','.zip','.rar'))]
        if valid and (query is None or any(query.casefold() in a.get_text(' ',strip=True).casefold() for a in valid)):
            return records,title,[{'title':a.get_text(' ',strip=True),'url':a['href']} for a in valid[:3]]
    return None


async def main(retry=False):
    async with httpx.AsyncClient(timeout=20,follow_redirects=False) as client:
        response=await client.get('https://fmhy.net/audio')
        response.raise_for_status()
        targets=targets_from_html(response.text)
    assert len(targets)>80,'FMHY extraction unexpectedly short'
    auditor=Auditor(8,10)
    output=ROOT/'docs'/'free-websites-audit.json'
    previous=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {'sources':[]}
    target_names = {t['name']:t['url'] for t in targets}
    records={r.get('requested_url',target_names.get(r['name'],r['url'])):r for r in previous['sources']}
    if retry:
        records={k:v for k,v in records.items() if v['outcome'] not in {'search_not_verified','inspection_error'}}
    presets_path=ROOT/'everytune'/'data'/'free_website_presets.json'
    presets={p['id']:p for p in json.loads(presets_path.read_text(encoding='utf-8'))} if presets_path.exists() else {}
    def save():
        output.write_text(json.dumps({'checked_at':now(),'sections':list(SECTIONS.values()),'total':len(targets),'completed':len(records),'complete':len(records)==len(targets),'outcomes':dict(Counter(r['outcome'] for r in records.values())),'sources':list(records.values())},ensure_ascii=False,indent=2),encoding='utf-8')
        presets_path.write_text(json.dumps(list(presets.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    async def inspect(target):
        record={**target,'requested_url':target['url'],'checked_at':now(),'free_access':'not_verified','integration':'not_verified'}
        host=urlsplit(target['url']).hostname
        try:
            if host in SKIP_HOSTS:
                record.update(outcome='not_a_direct_music_search',reason='Guide, community, repository or search index; not a music website connector.')
            else:
                async with asyncio.timeout(65):
                    page=await auditor.fetch(target['url'],1_000_000)
                    html=page.pop('body','')
                    record.update(page)
                    if page['outcome']=='fetched':
                        parser=PageParser(page['url']);parser.feed(html)
                        forms=parser.result()['get_search_forms']
                        record['forms']=forms
                        record['outcome']='no_public_get_search_observed' if not forms else 'search_not_verified'
                        for form in forms[:3]:
                            param=form['search_inputs'][0]
                            parts=urlsplit(form['action'])
                            fixed={**dict(parse_qsl(parts.query)),**form.get('fixed_params',{})}
                            if any(word in key.lower() for key in fixed for word in ('token','csrf','password','secret','api_key')):continue
                            query={'hip hop':'Eminem','metal':'Metallica','rock':'Beatles','electronic':'Tiesto','jazz':'Miles Davis','classical':'Bach','pop':'Madonna'}.get(target.get('genre_hint'),'Beatles')
                            search_url=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode({**fixed,param:query}),''))
                            result=await auditor.fetch(search_url,1_000_000)
                            body=result.pop('body','')
                            record.setdefault('searches',[]).append({**result,'query':query})
                            if result['outcome']!='fetched':continue
                            mapping=mapping_for_html(body,query)
                            if not mapping:
                                home_mapping=mapping_for_html(html)
                                if home_mapping and home_mapping[2]:
                                    title=home_mapping[2][0]['title']
                                    fallback=title.split(' – ',1)[0].split(' - ',1)[0].strip()[:70]
                                    if len(fallback)>=3 and fallback!=query:
                                        fallback_url=urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode({**fixed,param:fallback}),''))
                                        other=await auditor.fetch(fallback_url,1_000_000)
                                        other_body=other.pop('body','')
                                        record['searches'].append({**other,'query':fallback})
                                        if other['outcome']=='fetched':
                                            other_mapping=mapping_for_html(other_body,fallback)
                                            if other_mapping:
                                                result,body,mapping,query=other,other_body,other_mapping,fallback
                            if not mapping:continue
                            records_css,title_css,examples=mapping
                            # The result must contain the exact query, not just unrelated homepage articles.
                            if not any(query.casefold() in example['title'].casefold() for example in examples):continue
                            final=urlsplit(result['url'])
                            if final.scheme!='https':continue
                            endpoint=urlunsplit((final.scheme,final.netloc,final.path,'',''))
                            params=dict(parse_qsl(final.query));params.pop(param,None)
                            id='custom_web_'+hashlib.sha256(target['url'].encode()).hexdigest()[:10]
                            definition=SourceDefinition(id=id,name=target['name'],format='html',endpoint=endpoint,query_param=param,params=params,
                                results_path=records_css,fields={'title':title_css,'url':title_css+'@href'},kind='catalogue_post',category=target['sections'][0],limit_param=None,page_param=None,interval=1.5,ttl=3600)
                            presets[id]=definition.model_dump()
                            record.update(outcome='html_search_mapping_observed',integration='public_html_mapping_needs_runtime_check',free_access='anonymous_search_response_observed',examples=examples,preset_id=id)
                            break
        except Exception as error:
            record.update(outcome='inspection_error',error=type(error).__name__)
        records[target['url']]=record
        save()
        print(f'{len(records)}/{len(targets)} {record["outcome"]}',flush=True)
    queue=asyncio.Queue()
    for target in targets:
        if target['url'] not in records:queue.put_nowait(target)
    async def worker():
        while not queue.empty():
            target=queue.get_nowait()
            await inspect(target)
            queue.task_done()
    try:await asyncio.gather(*(worker() for _ in range(8)))
    finally:await auditor.client.aclose();save()
    print(json.dumps({'targets':len(targets),'presets':len(presets),'outcomes':Counter(r['outcome'] for r in records.values())}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retry-unverified',action='store_true')
    args=parser.parse_args()
    asyncio.run(main(args.retry_unverified))
