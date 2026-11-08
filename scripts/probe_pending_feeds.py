import json,pathlib,httpx,concurrent.futures,re
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
out=pathlib.Path('docs/pending-site-evidence')
def work(i):
 d=json.loads((out/f'{i:02d}.json').read_text(encoding='utf-8'));u=d['url']; d={k:v for k,v in d.items() if k not in ('forms','scripts')}
 try:
  r=httpx.get(urljoin(u,'/robots.txt'),follow_redirects=True,timeout=15);d['robots_status']=r.status_code;d['robots_text']=r.text if r.status_code==200 else '';rp=RobotFileParser();rp.parse(r.text.splitlines() if r.status_code==200 else []);d['robots']=rp.can_fetch('EveryTune',u)
  h=(out/f'{i:02d}.html').read_text(encoding='utf-8') if (out/f'{i:02d}.html').exists() else ''
  if 'blogger.com' in h:
   ep=urljoin(u,'/feeds/posts/default');d['feed_robots']=rp.can_fetch('EveryTune',ep)
   if d['feed_robots']:
    r=httpx.get(ep,params={'alt':'json','max-results':'1'},timeout=20);j=r.json();entry=j.get('feed',{}).get('entry',[]);d['feed_status']=r.status_code
    if entry:
     e=entry[0];words=re.findall(r'[^\W\d_]{4,}',e['title']['$t']);q=words[0] if words else 'music';r=httpx.get(ep,params={'alt':'json','max-results':'5','q':q},timeout=20);j=r.json();es=j.get('feed',{}).get('entry',[]);d['feed_query']=q;d['feed_matches']=[{'title':e['title']['$t'],'links':e['link']} for e in es];d['feed_endpoint']=ep
     (out/f'{i:02d}-search.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
     r=httpx.get(ep,params={'alt':'json','q':'EveryTuneImpossibleQuery78147814','max-results':'1'},timeout=20);d['empty_query_count']=len(r.json().get('feed',{}).get('entry',[]))
 except Exception as e:d['probe_error']=str(e)
 (out/f'{i:02d}-result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');return {k:v for k,v in d.items() if k not in ('robots_text','searchlinks','feed_matches')}
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
 for d in ex.map(work,[35,36,45,46,48,53,54,58,60,61,64,65,67,69]):print(json.dumps(d,ensure_ascii=True),flush=True)
