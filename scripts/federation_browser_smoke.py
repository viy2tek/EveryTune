"""Compare a live origin search with EveryTune and exercise the new POST connectors."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parent.parent
ARTIFACTS=ROOT/'artifacts'
with tempfile.TemporaryDirectory(prefix='everytune-federation-') as directory:
    process=subprocess.Popen([sys.executable,'-m','everytune','--port','0','--no-browser'],cwd=ROOT,env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    base=None
    try:
        base=re.search(r'http://127\.0\.0\.1:\d+',process.stdout.readline()).group()
        for _ in range(100):
            try:urllib.request.urlopen(base+'/api/health',timeout=1).close();break
            except OSError:time.sleep(.1)
        errors=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge' if sys.platform=='win32' else 'chromium',headless=True)
            origin=browser.new_page()
            origin.route('**/*',lambda route:route.abort() if route.request.resource_type in {'media','image','font'} or re.search(r'\.(mp3|mid|flac|zip)(\?|$)',route.request.url,re.I) else route.continue_())
            origin.goto('https://freemidi.org/',wait_until='domcontentloaded')
            origin.locator('input[name="q"]').first.fill('Beatles')
            origin.locator('input[name="q"]').first.press('Enter')
            expect(origin.locator('h1')).to_contain_text('Beatles',timeout=30000)
            origin.wait_for_load_state('domcontentloaded')
            origin_titles=[title.strip() for title in origin.locator('.card-title a').all_text_contents()]
            assert origin_titles
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0")
            page.locator('#options-toggle').click()
            expect(page.locator('#search-mode')).to_have_value('auto')
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('source')
            def only_source(id):
                page.evaluate('setSearchOptions(true)')
                for checkbox in page.locator('#source-list input').all():
                    if checkbox.is_enabled():checkbox.uncheck()
                page.locator(f'[data-source="{id}"] input').check()
            def search(query):
                page.locator('#query').fill(query)
                page.locator('#search-button').click()
                expect(page.locator('#cancel')).to_be_hidden(timeout=60000)
            only_source('custom_fed_449990f36e')
            search('Beatles')
            app_titles=page.locator('.track-info h3').all_text_contents()
            assert app_titles==origin_titles,(app_titles,origin_titles)
            assert set(page.locator('.match').all_text_contents())=={'Nomes não conferidos'}
            expect(page.locator('#interpretation')).to_contain_text('Texto enviado: “Beatles”')
            page.screenshot(path=str(ARTIFACTS/'federated-results.png'),animations='disabled')
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('track')
            search('Beatles')
            assert page.locator('.track-info h3').count()==0
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('source')
            only_source('custom_certifiedmixtapez')
            search('Gucci')
            assert page.locator('.track-group').count()>0
            expect(page.locator('#results')).to_contain_text('Certified Mixtapez')
            only_source('custom_fed_4ccff89824')
            search('Computerwife')
            assert page.locator('.track-group').count()>0
            page.locator('#nav-settings').click()
            page.get_by_role('button',name='Adicionar fontes',exact=True).click()
            expect(page.locator('#source-method')).to_be_visible()
            expect(page.locator('#source-encoding')).to_be_visible()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Mobile overflow'
            assert not errors,errors
            browser.close()
        (ARTIFACTS/'federation-browser-report.json').write_text(json.dumps({'origin_titles':origin_titles,'everytune_titles':app_titles,'checks':['origin_ui_order_equal','source_mode_badge','strict_mode_preserved','post_json_live','post_form_live','method_encoding_controls','mobile_no_overflow'],'javascript_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
        print('Federation browser smoke passed: live origin titles/order, raw vs exact, POST JSON/form, source editor and mobile; no JS errors.')
    finally:
        if base:
            try:
                urllib.request.urlopen(urllib.request.Request(base+'/api/shutdown',data=b'',headers={'X-EveryTune':'1'}),timeout=3).close()
                process.wait(timeout=15)
            except (OSError,subprocess.TimeoutExpired):pass
        if process.poll() is None:process.terminate();process.wait(timeout=10)
