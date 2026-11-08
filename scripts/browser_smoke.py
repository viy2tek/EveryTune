"""Optional UI check: pip install playwright, then use installed Edge or Chromium."""
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

root=Path(__file__).resolve().parent.parent
output=root/"artifacts"
output.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="everytune-ui-") as directory:
    process=subprocess.Popen([sys.executable,"-m","everytune","--port","0","--no-browser"],cwd=root,env={**os.environ,"EVERYTUNE_DATA_DIR":directory,"PYTHONIOENCODING":"utf-8"},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8")
    try:
        line=process.stdout.readline()
        base=re.search(r"http://127\.0\.0\.1:\d+",line).group()
        for _ in range(100):
            try:
                urllib.request.urlopen(base+"/api/health",timeout=1).close();break
            except OSError:time.sleep(.1)
        errors=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(channel="msedge" if sys.platform=="win32" else "chromium",headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1050})
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0")
            page.locator('#options-toggle').click()
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('auto')
            assert page.locator('.source-option').count()>=12
            page.screenshot(path=str(output/"desktop-initial.png"),full_page=True)
            page.locator('#query').fill('Daft Punk')
            page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=120000)
            assert page.locator('.track-group').count()>0
            page.screenshot(path=str(output/"desktop-results.png"),animations="disabled")
            page.locator('#filters summary').click()
            page.select_option('#filter-platform',label='iTunes / Apple')
            assert page.locator('.origin a').count()>0
            assert all('iTunes / Apple' in text for text in page.locator('.origin a').all_text_contents())
            page.select_option('#filter-platform',value='')
            external_before=page.locator('#external-links a').count()
            assert external_before>=11
            if page.locator('#more').is_visible():
                page.locator('#more').click()
                expect(page.locator('#cancel')).to_be_hidden(timeout=120000)
                assert page.locator('#external-links a').count()==external_before
            page.locator('#query').fill('Soft Pillow Kisses - Stolen Flowers')
            page.get_by_role('button',name='Buscar',exact=False).first.click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=120000)
            assert page.locator('.track-group').count()==0
            expect(page.locator('#results')).to_contain_text('Nenhuma correspondência confirmada.')
            expect(page.locator('#interpretation')).to_contain_text('Artista: “Soft Pillow Kisses”')
            assert page.get_by_text('Relacionada',exact=True).count()==0
            page.evaluate('setSearchOptions(true)')
            page.locator('#query').fill('')
            page.locator('#search-artist').fill('Daft Punk')
            page.locator('#search-title').fill('Get Lucky')
            page.get_by_role('button',name='Buscar',exact=False).first.click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=120000)
            assert page.locator('.track-group').count()>0
            assert set(page.locator('.track-info h3').all_text_contents())=={'Get Lucky'}
            expect(page.locator('#interpretation')).to_contain_text('Faixa: “Get Lucky”')
            page.screenshot(path=str(output/"desktop-precise.png"),animations="disabled")
            page.set_viewport_size({"width":390,"height":844})
            page.locator('.topbar').scroll_into_view_if_needed()
            page.screenshot(path=str(output/"mobile-results.png"),animations="disabled")
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'
            page.locator('#nav-settings').click()
            page.locator('#max-results').fill('5')
            page.locator('#pref-theme').select_option('dark')
            page.get_by_role('button',name='Fontes instaladas',exact=True).click()
            page.locator('[data-credential="lastfm_api_key"]').fill('UI-TEST-NOT-REAL')
            page.get_by_role('button',name='Salvar ajustes',exact=True).click()
            page.get_by_text('Ajustes salvos. Credenciais válidas somente nesta sessão.',exact=True).wait_for()
            assert page.locator('[data-credential="lastfm_api_key"]').input_value()==''
            assert 'UI-TEST-NOT-REAL' not in page.content()
            assert page.locator('html').get_attribute('data-theme')=='dark'
            page.get_by_role('button',name='Limpar cache',exact=True).click()
            page.get_by_role('button',name='Consultar logs',exact=True).click()
            page.locator('#logs').wait_for(state='visible')
            page.locator('.topbar').scroll_into_view_if_needed()
            page.screenshot(path=str(output/"mobile-settings.png"))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Settings overflow'
            assert not errors,errors
            browser.close()
        request=urllib.request.Request(base+"/api/shutdown",data=b"",headers={"X-EveryTune":"1"})
        urllib.request.urlopen(request,timeout=3).close()
        assert process.wait(timeout=15)==0
        (output/'browser-report.json').write_text(json.dumps({"checks":["desktop_search","platform_filter","pagination_preserves_external_links","irrelevant_results_rejected","explicit_artist_title_fields","mobile_no_overflow","settings_save","credential_not_echoed","clear_cache","logs","no_javascript_errors"],"javascript_errors":errors},indent=2),encoding='utf-8')
        print('Browser smoke passed: search, filters, pagination, settings, credentials, cache, logs, desktop and mobile; no JS errors.')
    finally:
        try:
            request=urllib.request.Request(base+"/api/shutdown",data=b"",headers={"X-EveryTune":"1"})
            urllib.request.urlopen(request,timeout=3).close()
            process.wait(timeout=10)
        except (OSError,NameError,subprocess.TimeoutExpired):pass
        if process.poll() is None:process.terminate();process.wait(timeout=10)
