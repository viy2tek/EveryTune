"""End-to-end UI verification for free websites, credits, editable connectors and profiles."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import expect,sync_playwright

ROOT=Path(__file__).resolve().parent.parent
ARTIFACTS=ROOT/'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='everytune-expanded-') as directory:
    process=subprocess.Popen([sys.executable,'-m','everytune','--port','0','--no-browser'],cwd=ROOT,env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    base=None
    try:
        line=process.stdout.readline()
        base=re.search(r'http://127\.0\.0\.1:\d+',line).group()
        for _ in range(100):
            try:urllib.request.urlopen(base+'/api/health',timeout=1).close();break
            except OSError:time.sleep(.1)
        errors=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge' if sys.platform=='win32' else 'chromium',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1050})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0")
            page.locator('#options-toggle').click()
            def only_source(id):
                page.evaluate('setSearchOptions(true)')
                for checkbox in page.locator('#source-list input').all():
                    if checkbox.is_enabled():checkbox.uncheck()
                page.locator(f'[data-source="{id}"] input').check()
            only_source('deezer')
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('credits')
            page.locator('#query').fill('viy2tek')
            page.get_by_role('button',name='Buscar',exact=False).first.click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=60000)
            assert page.locator('.track-group').count()>0
            expect(page.locator('#results')).to_contain_text('viy2tek')
            assert 'Vitek' not in page.locator('#results').inner_text()
            page.locator('.topbar').scroll_into_view_if_needed()
            page.screenshot(path=str(ARTIFACTS/'expanded-credits.png'),animations='disabled')
            only_source('custom_web_5262b0d57a')
            page.evaluate('setSearchOptions(true)')
            page.locator('#search-mode').select_option('auto')
            page.locator('#query').fill('Beatles')
            page.get_by_role('button',name='Buscar',exact=False).first.click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=60000)
            assert page.locator('.track-group').count()>0
            assert set(page.locator('.match').all_text_contents())=={'Menção em página'}
            page.locator('#nav-settings').click()
            page.locator('#pref-theme').select_option('dark')
            page.locator('#pref-view').select_option('grid')
            page.locator('#pref-country').fill('US')
            page.locator('#pref-artwork').uncheck()
            page.get_by_role('button',name='Salvar ajustes',exact=True).click()
            expect(page.locator('#save-status')).to_contain_text('Ajustes salvos')
            assert page.locator('html').get_attribute('data-theme')=='dark'
            page.get_by_role('button',name='Adicionar fontes',exact=True).click()
            page.locator('#source-name').fill('Catálogo grátis de teste')
            page.locator('#source-format').select_option('external')
            page.locator('#source-endpoint').fill('https://archive.org/advancedsearch.php')
            page.get_by_role('button',name='Salvar fonte',exact=True).click()
            expect(page.locator('#source-save-status')).to_contain_text('Fonte salva')
            page.get_by_role('button',name='Perfis',exact=True).click()
            with page.expect_download() as download_info:page.get_by_role('button',name='Exportar perfil',exact=True).click()
            path=ARTIFACTS/'test-export-profile.json'
            download_info.value.save_as(path)
            profile=json.loads(path.read_text(encoding='utf-8'))
            assert profile['settings']['theme']=='dark' and profile['settings']['country']=='US'
            assert any(s['name']=='Catálogo grátis de teste' for s in profile['sources'])
            assert 'secrets' not in profile and 'credentials' not in profile
            page.get_by_role('button',name='Fontes instaladas',exact=True).click()
            row=page.locator('.setting-source').filter(has_text='Catálogo grátis de teste')
            row.get_by_role('button',name='Remover',exact=True).click()
            expect(page.locator('.setting-source').filter(has_text='Catálogo grátis de teste')).to_have_count(0)
            page.get_by_role('button',name='Perfis',exact=True).click()
            page.locator('#import-profile').set_input_files(path)
            expect(page.locator('#profile-status')).to_contain_text('Perfil importado')
            page.get_by_role('button',name='Auditoria FMHY',exact=True).click()
            expect(page.locator('#audit-summary')).to_contain_text('124',timeout=10000)
            page.locator('#audit-query').fill('Hipstrumentals')
            page.get_by_role('button',name='Filtrar',exact=True).click()
            expect(page.locator('.audit-row')).to_have_count(1)
            page.screenshot(path=str(ARTIFACTS/'expanded-audit.png'),animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            page.locator('.topbar').scroll_into_view_if_needed()
            page.screenshot(path=str(ARTIFACTS/'expanded-mobile.png'),animations='disabled')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Mobile overflow'
            page.get_by_role('button',name='Perfis',exact=True).click()
            page.get_by_role('button',name='Restaurar padrões',exact=True).click()
            expect(page.locator('#profile-status')).to_contain_text('Padrões restaurados')
            assert page.locator('html').get_attribute('data-theme')=='light'
            assert not errors,errors
            browser.close()
        (ARTIFACTS/'expansion-browser-report.json').write_text(json.dumps({'checks':['deezer_exact_contributor','website_title_mention_label','theme_grid_country','create_remove_connector','export_import_without_secrets','selected_fmhy_audit','mobile_no_overflow','restore_defaults'],'javascript_errors':errors},indent=2),encoding='utf-8')
        print('Expansion browser smoke passed: free website search, credits, preferences, connectors, profiles, audit and mobile; no JS errors.')
    finally:
        if base:
            try:
                req=urllib.request.Request(base+'/api/shutdown',data=b'',headers={'X-EveryTune':'1'})
                urllib.request.urlopen(req,timeout=3).close();process.wait(timeout=15)
            except (OSError,subprocess.TimeoutExpired):pass
        if process.poll() is None:process.terminate();process.wait(timeout=10)
