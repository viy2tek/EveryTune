"""Real UI: provider focus and a ZIP of two public metadata XML files, never music."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from playwright.sync_api import expect,sync_playwright

ROOT=Path(__file__).resolve().parent.parent
ARTIFACTS=ROOT/'artifacts'
with tempfile.TemporaryDirectory(prefix='everytune-providers-ui-') as directory:
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
            page=browser.new_page(viewport={'width':1440,'height':1050},accept_downloads=True)
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0")
            page.locator('#options-toggle').click()
            expect(page.locator('[data-provider-group="streaming"]')).to_be_visible()
            expect(page.locator('[data-provider-group="community"]')).to_be_visible()
            page.get_by_role('button',name='Limpar de streaming',exact=True).click()
            page.get_by_role('button',name='Limpar de comunidade',exact=True).click()
            page.locator('[data-source="itunes"] input').check()
            page.locator('[data-source="archive"] input').check()
            page.locator('#provider-scope').select_option('streaming')
            assert page.locator('[data-source="archive"]').count()==0
            page.locator('#query').fill('Daft Punk')
            page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=60000)
            assert page.locator('.track-group').count()>0
            assert all('iTunes / Apple' in text for text in page.locator('.origin>a').all_text_contents())
            page.locator('#provider-scope').select_option('both')
            assert page.locator('#source-list input:checked').count()==2
            page.screenshot(path=str(ARTIFACTS/'provider-groups.png'),animations='disabled')
            page.evaluate('setSearchOptions(true)')
            page.locator('[data-source="itunes"] input').uncheck()
            page.locator('#provider-scope').select_option('community')
            page.locator('#query').fill('sam torres still')
            page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden(timeout=60000)
            page.locator('#nav-settings').click()
            page.locator('[data-panel="custom"]').click()
            page.locator('.download-inspect summary').click()
            page.locator('#download-inspect-source').select_option('archive')
            page.locator('#download-inspect-url').fill('https://archive.org/details/sam-torres-still')
            page.locator('#download-inspect-form button').click()
            expect(page.locator('#download-manifest')).to_be_visible(timeout=60000)
            for filename in ('sam-torres-still_files.xml','sam-torres-still_meta.xml'):
                row=page.locator('.download-option').filter(has=page.locator('.download-option-info>p').filter(has_text=filename))
                expect(row).to_have_count(1)
                row.locator('input').check()
            expect(page.locator('#download-selection-count')).to_have_text('2 arquivos selecionados')
            page.locator('#download-zip').click()
            save=page.locator('#download-jobs').get_by_role('link',name='Salvar arquivo',exact=True)
            expect(save).to_be_visible(timeout=90000)
            with page.expect_download(timeout=30000) as event:save.click()
            download=event.value
            target=ARTIFACTS/'selected-metadata.zip';download.save_as(target)
            with zipfile.ZipFile(target) as bundle:
                assert set(bundle.namelist())=={'sam-torres-still_files.xml','sam-torres-still_meta.xml'}
                assert all(bundle.read(name).lstrip().startswith(b'<?xml') for name in bundle.namelist())
            page.screenshot(path=str(ARTIFACTS/'selected-downloads.png'),animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Mobile page overflow'
            assert page.locator('#download-dialog').evaluate('(node)=>node.scrollWidth<=node.clientWidth'),'Mobile dialog overflow'
            page.screenshot(path=str(ARTIFACTS/'downloads-mobile.png'),animations='disabled')
            page.locator('#download-close').click()
            page.locator('#nav-settings').click()
            page.locator('#pref-scope').select_option('community')
            page.locator('#pref-download-limit').fill('512')
            page.get_by_role('button',name='Salvar ajustes',exact=True).click()
            expect(page.locator('#save-status')).to_contain_text('Ajustes salvos')
            page.reload()
            expect(page.locator('#provider-scope')).to_have_value('community')
            assert page.locator('[data-provider-group="streaming"]').count()==0
            assert not errors,errors
            browser.close()
        (ARTIFACTS/'providers-download-browser-report.json').write_text(json.dumps({'checks':['provider_groups','streaming_only_query','selections_preserved_across_focus','community_query','actual_archive_file_manifest','select_two_metadata_files','prepare_zip','browser_save_zip','zip_contains_only_selected_xml','mobile','preferences_persist'],'javascript_errors':errors,'downloaded_music':False},indent=2),encoding='utf-8')
        print('Provider/download browser smoke passed: grouping, focus, two selected XML files, real ZIP save, mobile and preferences; no music transferred.')
    finally:
        if base:
            try:
                urllib.request.urlopen(urllib.request.Request(base+'/api/shutdown',data=b'',headers={'X-EveryTune':'1'}),timeout=3).close();process.wait(timeout=15)
            except (OSError,subprocess.TimeoutExpired):pass
        if process.poll() is None:process.terminate();process.wait(timeout=10)
