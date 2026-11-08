"""Focused audit follow-up: nested overflow, keyboard order, zoom and spacing."""
import ast
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
tree=ast.parse((ROOT/'scripts/audit_ux_layout.py').read_text(encoding='utf-8'))
snippets={node.targets[0].id:ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'MEASURE','FIXTURE'}}
result={}
with tempfile.TemporaryDirectory(prefix='everytune-ux-followup-') as directory:
 process=subprocess.Popen([sys.executable,'-m','everytune','--port','0','--no-browser'],cwd=ROOT,env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
 base=None
 try:
  base=re.search(r'http://127\.0\.0\.1:\d+',process.stdout.readline()).group()
  for _ in range(100):
   try:urllib.request.urlopen(base+'/api/health',timeout=1).close();break
   except OSError:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(channel='msedge',headless=True)
   page=browser.new_page(viewport={'width':320,'height':800})
   page.route('**/api/downloads/jobs',lambda r:r.fulfill(json=[]))
   page.goto(base);page.locator('[data-source="spotify"]').wait_for()
   result['source_scroller_320']=page.locator('#source-list').evaluate('(n)=>({width:n.clientWidth,scrollWidth:n.scrollWidth,height:n.clientHeight,scrollHeight:n.scrollHeight,overflowX:getComputedStyle(n).overflowX,overflowY:getComputedStyle(n).overflowY})')
   page.locator('#source-list').evaluate('(n)=>n.scrollTop=0')
   page.locator('.source-sidebar').scroll_into_view_if_needed()
   page.screenshot(path=str(OUT/'source-panel-320.png'),animations='disabled')
   result['mobile_status']=page.locator('[data-source="spotify"] .state').evaluate('(n)=>({text:n.textContent,display:getComputedStyle(n).display})')
   page.set_viewport_size({'width':1440,'height':1000});page.evaluate(snippets['FIXTURE'],12)
   result['keyboard_order']=page.evaluate('''() => {const items=[...document.querySelectorAll('button,input,select,textarea,summary,a[href]')].filter(n=>n.tabIndex>=0&&!n.disabled&&n.getClientRects().length);return {queryIndex:items.indexOf($('query')),firstResultIndex:items.indexOf(document.querySelector('.origin>a')),sourcesBeforeResult:items.slice(0,items.indexOf(document.querySelector('.origin>a'))).filter(n=>n.closest('#source-list')).length};}''')
   result['borders']=page.locator('#query').evaluate('''n=>{const s=getComputedStyle(n);const m=getComputedStyle(document.querySelector('.searchbox'));return {inputBorder:s.borderColor,wrapperBorder:m.borderColor,background:m.backgroundColor};}''')
   page.locator('#nav-settings').click()
   page.locator('[data-panel="preferences"]').click()
   result['preference_border']=page.locator('#pref-country').evaluate('(n)=>({border:getComputedStyle(n).borderColor,bg:getComputedStyle(n).backgroundColor})')
   page.evaluate("settings.theme='dark';applyPreferences();renderSettings()")
   result['dark_button']=page.locator('#settings-form button[type=submit]').evaluate('(n)=>({bg:getComputedStyle(n).backgroundColor,color:getComputedStyle(n).color})')
   page.screenshot(path=str(OUT/'settings-dark-confirmed.png'),animations='disabled')
   page.evaluate("settings.theme='light';applyPreferences();renderSettings()")
   page.set_viewport_size({'width':320,'height':800});page.locator('[data-panel="custom"]').click()
   page.evaluate("document.styleSheets[0].insertRule('* {line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}',0);document.styleSheets[0].insertRule('p {margin-bottom:2em!important}',0)")
   result['text_spacing_320']=page.evaluate(snippets['MEASURE']);page.screenshot(path=str(OUT/'text-spacing-320.png'),full_page=True,animations='disabled')
   page.reload();page.locator('[data-source="spotify"]').wait_for()
   page.set_viewport_size({'width':1280,'height':900})
   page.evaluate("document.styleSheets[0].insertRule('html {font-size:200%!important}',0)")
   result['text_resize_200']=page.evaluate(snippets['MEASURE']);page.screenshot(path=str(OUT/'text-resize-200.png'),full_page=True,animations='disabled')
   browser.close()
 finally:
  (OUT/'followup.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  if base:
   try:urllib.request.urlopen(urllib.request.Request(base+'/api/shutdown',data=b'',headers={'X-EveryTune':'1'}),timeout=3).close();process.wait(timeout=15)
   except (OSError,subprocess.TimeoutExpired):pass
  if process.poll() is None:process.terminate();process.wait(timeout=10)
print('Focused measurements saved')
