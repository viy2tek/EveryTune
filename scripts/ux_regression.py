"""Browser regressions for R01–R13, using isolated data and metadata-only fixtures."""
import argparse
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

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'artifacts/ux-fixes-2026-11-06'
OUT.mkdir(exist_ok=True)
tree = ast.parse((ROOT / 'scripts/audit_ux_layout.py').read_text(encoding='utf-8'))
fixture_nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in {'FIXTURE', 'manifest', 'job'}]
values = {}
exec(compile(ast.Module(body=fixture_nodes,type_ignores=[]),'controlled-fixtures','exec'),values)
parser = argparse.ArgumentParser()
parser.add_argument('--executable')
args = parser.parse_args()
report = {'target': args.executable or 'Python source', 'checks': [], 'screens': [], 'errors': []}


def checked(name):
    report['checks'].append(name)


with tempfile.TemporaryDirectory(prefix='everytune-ux-fixes-') as directory:
    command = [args.executable] if args.executable else [sys.executable, '-m', 'everytune']
    process = subprocess.Popen(command + ['--port', '0', '--no-browser'], cwd=ROOT,
        env={**os.environ, 'EVERYTUNE_DATA_DIR': directory, 'PYTHONIOENCODING': 'utf-8'},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8',errors='replace')
    try:
        startup=[]
        for line in process.stdout:
            startup.append(line)
            match=re.search(r'http://127\.0\.0\.1:\d+',line)
            if match:
                base=match.group()
                break
        else:
            raise RuntimeError('Application did not start: '+''.join(startup))
        for _ in range(100):
            try:
                urllib.request.urlopen(base + '/api/health', timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width':1440, 'height':1000}, accept_downloads=True)
            page.on('pageerror', lambda e: report['errors'].append(str(e)))
            job = dict(values['job'])
            page.route('**/api/downloads/jobs', lambda r: r.fulfill(json=[job]))
            page.route('**/api/downloads/prepare', lambda r: r.fulfill(json=job))
            page.route('**/api/downloads/resolve/*', lambda r: r.fulfill(json=values['manifest']))
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0")
            for width, height in [(1440,1000),(1024,768),(768,1024),(600,900),(390,844),(320,800)]:
                page.set_viewport_size({'width':width, 'height':height})
                page.evaluate(values['FIXTURE'],12)
                for theme in ['light','dark']:
                    page.evaluate('(theme)=>{settings.theme=theme;applyPreferences()}',theme)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                    name=f'results-{width}-{theme}.png'
                    page.screenshot(path=str(OUT/name), full_page=True, animations='disabled')
                    report['screens'].append(name)
                if width<=700:
                    assert page.locator('#source-controls').is_hidden()
                    top=page.locator('.results-area').bounding_box()['y']
                    assert top<height, (width,top)
                    assert page.locator('.track-group').first.bounding_box()['y']<height, width
                    page.locator('#options-toggle').click()
                    assert page.locator('#source-list').evaluate('n=>n.scrollWidth<=n.clientWidth')
                    expect(page.locator('[data-source="soundcloud"] .state')).to_be_visible()
                    assert page.locator('.provider-actions button').first.bounding_box()['height']>=43.5
                    page.locator('#options-toggle').click()
            checked('R02/R03/R07/R09/R10: responsive, source status, targets, results in viewport')
            page.set_viewport_size({'width':1440,'height':1000})
            page.evaluate("settings.theme='light';applyPreferences()")
            page.locator('.origin>a').first.focus()
            page.evaluate("handleEvent({type:'source',source:'itunes',name:'iTunes',status:'success',tracks:[]})")
            assert page.locator('.origin>a').first.evaluate('n=>n===document.activeElement')
            page.evaluate("tracks[0].album='Updated metadata';renderResults()")
            assert page.locator('.origin>a').first.evaluate('n=>n===document.activeElement')
            page.evaluate("tracks.push({...tracks[0],source_id:'new',group:'new',score:999});renderResults()")
            assert page.evaluate("document.activeElement.dataset.focusKey==='origin:itunes:0'")
            checked('R01: result focus survives unchanged, changed and reordered cards')
            page.evaluate("foundPeople.set('fixture:1',{source:'musicbrainz_credits',id:'fixture',name:'Pessoa de teste',url:'https://example.org/person'});renderPeople()")
            page.locator('.person-row button').focus()
            page.evaluate("handleEvent({type:'source',source:'itunes',name:'iTunes',status:'success',tracks:[]})")
            assert page.locator('.person-row button').evaluate('n=>n===document.activeElement')
            page.evaluate('foundPeople.clear();renderPeople()')
            page.locator('a[href="#results-title"]').focus()
            page.keyboard.press('Enter')
            assert page.locator('#results-title').evaluate('n=>n===document.activeElement')
            checked('R08: direct keyboard shortcut to results')
            page.evaluate('setSearchOptions(true)')
            page.locator('#manage-sources').click()
            expect(page.locator('#panel-sources')).to_be_visible()
            checked('R11: manage sources opens sources panel')
            page.locator('[data-panel="custom"]').click()
            expect(page.locator('#source-encoding')).to_be_hidden()
            expect(page.locator('#source-auth-name')).to_be_hidden()
            page.locator('#source-method').select_option('POST')
            expect(page.locator('#source-encoding')).to_be_visible()
            page.locator('#source-auth').select_option('header')
            expect(page.locator('#source-auth-name')).to_be_visible()
            page.locator('#source-format').select_option('external')
            for field in ['source-method','source-auth','source-auth-name','source-results-path','source-field-title','source-encoding']:
                expect(page.locator('#'+field)).to_be_hidden()
            page.locator('#source-format').select_option('html')
            expect(page.locator('#source-encoding')).to_be_visible()
            expect(page.locator('#source-auth-name')).to_be_visible()
            page.locator('#source-format').select_option('external')
            page.locator('#source-name').fill('UX saved source')
            page.locator('#source-endpoint').fill('https://example.org/search')
            page.locator('#custom-source-form button[type=submit]').click()
            expect(page.locator('#source-save-status')).to_contain_text('Fonte salva')
            saved=page.evaluate("async()=>await(await api('/api/custom-sources')).json()")
            source=next(s for s in saved if s['name']=='UX saved source')
            assert source['method']=='GET' and source['auth']=='none'
            checked('R12: emitted Bend policy drives editor; hidden settings do not leak into external definition')
            page.locator('[data-panel="profiles"]').click()
            page.locator('#reset-profile').click()
            expect(page.locator('#reset-dialog')).to_be_visible()
            assert page.evaluate('document.activeElement.id')=='reset-cancel'
            page.keyboard.press('Escape')
            saved=page.evaluate("async()=>await(await api('/api/custom-sources')).json()")
            assert any(s['name']=='UX saved source' for s in saved)
            page.locator('#reset-profile').click()
            with page.expect_download() as download_info:
                page.locator('#reset-backup').click()
            backup=json.loads(Path(download_info.value.path()).read_text(encoding='utf-8'))
            assert 'UX saved source' in json.dumps(backup)
            page.locator('#reset-confirm').click()
            expect(page.locator('#reset-dialog')).not_to_be_visible()
            expect(page.locator('#profile-status')).to_contain_text('Padrões restaurados')
            assert not any(s['name']=='UX saved source' for s in page.evaluate("async()=>await(await api('/api/custom-sources')).json()"))
            checked('R04: cancel is safe; backup includes source; only explicit confirmation resets isolated data')
            page.locator('[data-panel="preferences"]').click()
            border=page.locator('#pref-country').evaluate('n=>getComputedStyle(n).borderColor')
            assert border=='rgb(123, 137, 127)',border
            checked('R06: stronger control border applied')
            page.locator('#nav-search').click()
            page.evaluate(values['FIXTURE'],12)
            files=page.locator('.origin button').first
            files.click()
            expect(page.locator('#download-manifest')).to_be_visible()
            page.locator('.download-option-info').first.click()
            expect(page.locator('.download-option input').first).to_be_checked()
            assert 'Nome de arquivo' in page.locator('.download-option>button').first.get_attribute('aria-label')
            page.locator('.download-option>button').first.click()
            action=page.locator('.download-job-actions button').first
            action.focus()
            page.wait_for_timeout(1300)
            assert action.evaluate('n=>n===document.activeElement')
            announcement=page.locator('#download-job-status').text_content()
            job['bytes']+=1000
            page.wait_for_timeout(1300)
            assert page.locator('#download-job-status').text_content()==announcement
            job['status']='ready'
            expect(page.locator('.download-save')).to_be_visible(timeout=4000)
            expect(page.locator('#download-job-status')).to_contain_text('Pronto para salvar')
            assert page.locator('.download-job-actions button').evaluate('n=>n===document.activeElement')
            page.set_viewport_size({'width':390,'height':844})
            page.screenshot(path=str(OUT/'downloads-390.png'),full_page=True)
            page.keyboard.press('Escape')
            assert files.evaluate('n=>n===document.activeElement')
            checked('R01/R05/R10/R13: stable queue focus, transition announcements, clickable file labels, contextual names, dialog return')
            for panel in ['preferences','sources','custom','profiles']:
                page.locator('#nav-settings').click()
                page.locator(f'[data-panel="{panel}"]').click()
                for width in [1440,768,320]:
                    page.set_viewport_size({'width':width,'height':900})
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(panel,width)
                page.screenshot(path=str(OUT/f'settings-{panel}-320.png'),full_page=True)
            checked('Settings panels: no global overflow at desktop/tablet/mobile')
            assert not report['errors'], report['errors']
            browser.close()
    finally:
        (OUT/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        try:
            request=urllib.request.Request(base+'/api/shutdown',data=b'{}',headers={'Content-Type':'application/json','X-EveryTune':'1'},method='POST')
            urllib.request.urlopen(request,timeout=2).close()
            process.wait(timeout=10)
        except Exception:
            process.terminate()
print(json.dumps(report,ensure_ascii=False,indent=2))
