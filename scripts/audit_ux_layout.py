"""Read-only UX inspection of isolated app data, viewports and controlled UI states."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/ux-audit-2026-11-06'
OUT.mkdir(exist_ok=True)

MEASURE=r'''() => {
 const visible=n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};
 const rect=n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};};
 const info=n=>({tag:n.tagName,id:n.id,cls:typeof n.className==='string'?n.className:'',text:(n.innerText||n.getAttribute('aria-label')||n.name||'').slice(0,100),...rect(n)});
 const controls=[...document.querySelectorAll('button,a[href],input,select,textarea,summary')].filter(visible);
 const clips=[...document.querySelectorAll('h1,h2,h3,p,span,strong,button,label,select')].filter(n=>visible(n)&&n.scrollWidth>n.clientWidth+2&&getComputedStyle(n).overflowX!=='visible').map(info);
 const overflow=[...document.querySelectorAll('body *')].filter(n=>visible(n)&&n.getBoundingClientRect().right>innerWidth+2&&!n.closest('[hidden]')).map(info);
 const text=[...document.querySelectorAll('button,a,p,label,h1,h2,h3,span,strong,summary,select')].filter(n=>visible(n)&&n.textContent.trim()).map(n=>{const s=getComputedStyle(n);let p=n,bg='';while(p){const c=getComputedStyle(p).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent'){bg=c;break;}p=p.parentElement;}return {...info(n),color:s.color,bg,font:s.fontSize,weight:s.fontWeight,line:s.lineHeight,opacity:s.opacity};});
 return {viewport:{w:innerWidth,h:innerHeight,dpr:devicePixelRatio},scrollWidth:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,controls:controls.map(n=>{const label=n.labels?.[0];return {...info(n),effective:rect(label&&label.getBoundingClientRect().width*label.getBoundingClientRect().height>n.getBoundingClientRect().width*n.getBoundingClientRect().height?label:n),disabled:n.disabled||false};}),clips,overflow:overflow.slice(0,30),text,main:rect(document.querySelector('main')),results:rect(document.querySelector('.results-area')),sidebar:rect(document.querySelector('.source-sidebar'))};
}'''

FIXTURE=r'''count => {
 activeQuery='Produtor de exemplo';activeFields={mode:'source'};controller=null;
 tracks=Array.from({length:count},(_,i)=>({source:i%2?'archive':'itunes',source_id:String(i),platform:i%2?'Internet Archive':'iTunes / Apple',provider_group:i%2?'community':'streaming',category:i%2?'Acervos':'Comercial',title:i===0?'Nome de faixa extenso para verificar a quebra de linha e a relação entre título, créditos e botões':'Faixa de exemplo '+(i+1),artist:'Artista principal e colaboração',album:'Álbum de exemplo',artwork:'/static/icon.svg',year:'2026',duration:185,url:'https://example.org/item/'+i,kind:'track',score:0,matched_on:'source',group:'fixture-'+i,credits:i===0?[{name:'Nome do produtor',role:'Producer',evidence_url:'https://example.org/credits'}]:[],audio_available:true,download_ref:'fixture_download_reference_123'}));
 document.body.classList.add('has-search');$('results-title').textContent='Resultados para “Produtor de exemplo”';$('interpretation').hidden=false;$('interpretation').textContent='Resultados retornados pelas fontes, sem conferência de nomes.';renderResults();
}'''

manifest={'ref':'fixture_download_reference_123','source':'Fonte de exemplo','title':'Álbum com nome comprido e múltiplos discos','page_url':'https://example.org/album','license':None,'notices':['Links identificados na origem. Disponibilidade será conferida ao preparar o arquivo.'],'options':[{'id':f'option_{i}','filename':('01 - Nome de arquivo muito extenso ' * 3)+f'{i}.flac','label':f'Arquivo {i+1} · FLAC original','format':'FLAC','size':50_000_000,'kind':'audio','delivery':'direct','open_url':None} for i in range(8)]+[{'id':'mirror','filename':'Página do espelho','label':'FLAC no espelho externo','format':'FLAC','size':None,'kind':'other','delivery':'external','open_url':'https://example.org/mirror'}]}
job={'id':'fixture_job_reference_12345','source':'archive','title':'Álbum','filename':'Álbum selecionado.zip','status':'running','bytes':32_000_000,'total_bytes':100_000_000,'files_done':1,'files_total':4,'message':None,'pack':'zip'}

with tempfile.TemporaryDirectory(prefix='everytune-ux-audit-') as directory:
 process=subprocess.Popen([sys.executable,'-m','everytune','--port','0','--no-browser'],cwd=ROOT,env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
 base=None;report={'states':{},'errors':[]}
 try:
  base=re.search(r'http://127\.0\.0\.1:\d+',process.stdout.readline()).group()
  for _ in range(100):
   try:urllib.request.urlopen(base+'/api/health',timeout=1).close();break
   except OSError:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge' if sys.platform=='win32' else 'chromium',headless=True)
   page=browser.new_page(viewport={'width':1440,'height':1000})
   page.on('pageerror',lambda e:report['errors'].append(str(e)))
   page.route('**/api/downloads/resolve/*',lambda route:route.fulfill(json=manifest))
   page.route('**/api/downloads/jobs',lambda route:route.fulfill(json=[job]))
   page.goto(base);page.locator('[data-source="spotify"]').wait_for()
   def capture(name,full=False):
    report['states'][name]=page.evaluate(MEASURE)
    page.screenshot(path=str(OUT/(name+'.png')),full_page=full,animations='disabled')
   report['initial_navigation']=page.evaluate('''() => ({navigation:performance.getEntriesByType('navigation')[0].toJSON(),resources:performance.getEntriesByType('resource').map(r=>({name:r.name.split('/').pop(),bytes:r.transferSize,duration:r.duration})),nodes:document.querySelectorAll('*').length})''')
   for width,height in [(1440,1000),(1024,768),(768,1024),(600,900),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height})
    for theme in ['light','dark']:
     page.evaluate('(theme)=>{settings.theme=theme;applyPreferences()}',theme)
     page.evaluate('scrollTo(0,0)');capture(f'initial-{width}-{theme}')
   page.set_viewport_size({'width':1440,'height':1000});page.evaluate("settings.theme='light';applyPreferences()")
   page.evaluate(FIXTURE,12);page.evaluate('scrollTo(0,0)');capture('results-desktop',True)
   page.locator('.origin>a').first.focus()
   report['focus_before_result_update']=page.evaluate('document.activeElement.outerHTML')
   page.evaluate("handleEvent({type:'source',source:'archive',name:'Internet Archive',status:'success',tracks:[],people:[],notices:[],next_cursor:null,rejected_count:0})")
   report['focus_after_result_update']=page.evaluate('document.activeElement.tagName')
   for width,height in [(768,1024),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('scrollTo(0,0)');capture(f'results-{width}')
   page.set_viewport_size({'width':1440,'height':1000})
   report['render_performance']=page.evaluate('''() => {const out=[];for(const count of [30,150,500]){const source=tracks[0];tracks=Array.from({length:count},(_,i)=>({...source,source_id:String(i),group:'stress-'+i}));const start=performance.now();renderResults();out.push({count,render_ms:performance.now()-start,nodes:document.querySelectorAll('*').length});}return out;}''')
   page.evaluate(FIXTURE,3)
   for width,height in [(1440,1000),(768,1024),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height});page.locator('#nav-settings').click()
    for panel in ['preferences','sources','custom','audit','profiles']:
     page.locator(f'[data-panel="{panel}"]').click()
     if panel=='audit':page.locator('.audit-row').first.wait_for()
     page.evaluate('scrollTo(0,0)');capture(f'settings-{panel}-{width}',panel=='preferences')
   page.set_viewport_size({'width':1440,'height':1000})
   page.locator('[data-panel="preferences"]').click()
   page.evaluate("settings.theme='dark';applyPreferences()")
   capture('settings-dark')
   page.evaluate("settings.theme='light';applyPreferences()")
   page.locator('#nav-search').click()
   page.evaluate(FIXTURE,3)
   page.locator('.origin button').first.click();page.locator('.download-option').first.wait_for()
   page.locator('#download-jobs button').first.focus()
   report['focus_before_job_poll']=page.evaluate('document.activeElement.outerHTML')
   page.wait_for_timeout(1300)
   report['focus_after_job_poll']=page.evaluate('document.activeElement.tagName')
   for width,height in [(1440,1000),(768,1024),(390,844),(320,800)]:
    page.set_viewport_size({'width':width,'height':height})
    for theme in ['light','dark']:
     page.evaluate('(theme)=>{settings.theme=theme;applyPreferences()}',theme)
     page.locator('#download-dialog').evaluate('(n)=>n.scrollTop=0');capture(f'downloads-{width}-{theme}')
   page.set_viewport_size({'width':390,'height':844});page.evaluate("settings.theme='light';applyPreferences()")
   page.locator('#download-options input').first.focus()
   report['checkbox_focus_visible']=page.locator('#download-options input').first.evaluate('(n)=>{const s=getComputedStyle(n);return {outline:s.outline,rect:n.getBoundingClientRect().toJSON()}}')
   page.keyboard.press('Escape');report['dialog_escape_closed']=not page.locator('#download-dialog').evaluate('(n)=>n.open')
   page.set_viewport_size({'width':320,'height':800});page.evaluate('scrollTo(0,0)');page.locator('#nav-settings').click();page.locator('[data-panel="custom"]').click()
   page.evaluate("document.styleSheets[0].insertRule('*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}',0);document.styleSheets[0].insertRule('p{margin-bottom:2em!important}',0)")
   capture('text-spacing-320')
   browser.close()
 finally:
  (OUT/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
  if base:
   try:urllib.request.urlopen(urllib.request.Request(base+'/api/shutdown',data=b'',headers={'X-EveryTune':'1'}),timeout=3).close();process.wait(timeout=15)
   except (OSError,subprocess.TimeoutExpired):pass
  if process.poll() is None:process.terminate();process.wait(timeout=10)
print('UX screenshots and measurements saved to',OUT)
