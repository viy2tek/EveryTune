"""Bend-generated home, contextual files and queue regressions in isolated data."""
import argparse
import ast
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from playwright.sync_api import expect,sync_playwright

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/home-redesign-2026-11-06'
OUT.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--executable',type=Path);args=parser.parse_args()
tree=ast.parse((ROOT/'scripts/audit_ux_layout.py').read_text(encoding='utf-8'))
nodes=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'FIXTURE','manifest','job'}]
fixtures={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'controlled-fixtures','exec'),fixtures)
fixtures['manifest']['options'] += [
    {'id':'image_1','filename':'cover.jpg','label':'Capa','format':'JPG','kind':'artwork','size':2300,'delivery':'direct','open_url':None},
    {'id':'document_1','filename':'book.pdf','label':'PDF excluído','format':'PDF','kind':'document','size':100,'delivery':'direct','open_url':None}]
fixtures['manifest']['options'][0]['quality']={'bit_rate':320000,'sample_rate':44100}
report={'target':str(args.executable or 'Python source'),'checks':[],'errors':[]}
with tempfile.TemporaryDirectory(prefix='everytune-home-ui-') as directory:
    command=[str(args.executable.resolve())] if args.executable else [sys.executable,'-m','everytune']
    process=subprocess.Popen(command+['--port','0','--no-browser'],cwd=ROOT,env={**os.environ,'EVERYTUNE_DATA_DIR':directory,'PYTHONIOENCODING':'utf-8'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    lines=queue.Queue()
    def drain():
        for line in process.stdout:lines.put(line)
    threading.Thread(target=drain,daemon=True).start();base=None
    try:
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Server exited')
            try:line=lines.get(timeout=.2)
            except queue.Empty:continue
            match=re.search(r'http://127\.0\.0\.1:\d+',line)
            if match:base=match.group();break
        assert base
        for _ in range(100):
            try:urllib.request.urlopen(base+'/api/health',timeout=1).close();break
            except OSError:time.sleep(.1)
        jobs=[];preparations=[];queries=[];deferred=[];fail_option=None
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
            page.on('pageerror',lambda error:report['errors'].append(str(error)))
            page.route('**/api/downloads/jobs',lambda r:r.fulfill(json=jobs))
            page.route('**/api/downloads/resolve/*',lambda r:r.fulfill(json=fixtures['manifest']))
            def prepare(route):
                preparations.append(route.request.post_data_json)
                if fail_option and fail_option in route.request.post_data_json['option_ids']:
                    route.fulfill(status=422,json={'detail':'Falha controlada na seleção'});return
                job={**fixtures['job'],'id':'job-'+str(len(jobs)+1)};jobs.append(job);route.fulfill(json=job)
            page.route('**/api/downloads/prepare',prepare)
            def search(route):
                body=route.request.post_data_json;queries.append(body)
                track={'source':'archive','source_id':'verified','platform':'Internet Archive','category':'Acervos','title':'Verified test title','artist':'Artist','url':'https://example.org/one','group':'verified','score':1,'matched_on':'artist_title','audio_available':True}
                tracks=[track]
                if body['query']=='Grouped':
                    track.update(recording_group='same-recording',audio_formats=['FLAC'],audio_file_count=1)
                    tracks += [{**track,'source':'audius','source_id':'second','platform':'Audius','audio_formats':['MP3']},
                        {**track,'source_id':'remix','title':'Verified test title (Remix)','recording_group':'remix'}]
                source={'type':'source','source':'archive','name':'Internet Archive','status':'success','tracks':tracks}
                skipped=[]
                if body['query']=='No audio':
                    source.update(status='no_match',tracks=[],diagnostics={'name_or_version':2,'no_audio':3,'audio_check_failed':1,'audio_check_timeout':1})
                    skipped=[{'source':'itunes','name':'iTunes','reason':'catalogue'}]
                events=[{'type':'start','total':1,'external':[],'skipped':skipped,'interpretation':{'mode':body['mode'],'artist':'Artist','title':'Verified test title','text':body['query']}},source,{'type':'complete','tracks':source['tracks'],'sources':[source],'first_audio_ms':25}]
                if body['query'].startswith('Deferred'):
                    deferred.append((route,events));return
                route.fulfill(content_type='application/x-ndjson',body='\n'.join(json.dumps(e) for e in events)+'\n')
            page.route('**/api/search/stream',search)
            page.goto(base)
            page.wait_for_function("typeof window.showFiles==='function' && catalogue.length>0 && typeof Home==='object'")
            expect(page.locator('.results-area')).to_be_hidden()
            expect(page.locator('#source-controls')).to_be_hidden()
            expect(page.locator('#search-summary')).to_contain_text('nomes conferidos')
            assert not page.locator('.intro,.suggestions,.source-sidebar').count()
            for width,height in [(1440,1000),(768,1024),(390,844),(320,800)]:
                page.set_viewport_size({'width':width,'height':height})
                for theme in ['light','dark']:
                    page.evaluate('(theme)=>{settings.theme=theme;applyPreferences()}',theme)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
                    page.screenshot(path=str(OUT/f'initial-{width}-{theme}.png'),animations='disabled')
            report['checks'].append('Initial home: single search, no sidebar or empty illustration; desktop/mobile themes without overflow')
            page.set_viewport_size({'width':1440,'height':1000})
            page.locator('#options-toggle').click()
            expect(page.locator('#source-controls')).to_be_visible()
            expect(page.locator('#options-toggle')).to_have_attribute('aria-expanded','true')
            page.get_by_role('button',name='Limpar de streaming',exact=True).click()
            page.get_by_role('button',name='Limpar de comunidade',exact=True).click()
            page.locator('[data-source="audius"] input').check()
            page.locator('[data-source="archive"] input').check()
            page.locator('#provider-scope').select_option('streaming')
            assert page.locator('[data-source="archive"]').count()==0
            page.locator('#provider-scope').select_option('both')
            assert page.locator('#source-list input:checked').count()==2
            page.locator('#search-mode').select_option('credits')
            expect(page.locator('#search-summary')).to_contain_text('pessoa e créditos')
            page.locator('#search-mode').select_option('auto')
            page.locator('#options-toggle').click()
            report['checks'].append('Focus groups and individual selections preserved; credits discoverable; disclosure semantics')
            page.locator('#query').fill('Artist - Verified test title');page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden()
            expect(page.locator('.track-info h3')).to_have_text('Verified test title')
            assert queries[-1]['mode']=='auto' and queries[-1]['exclude_covers'] is True
            assert set(queries[-1]['sources'])=={'audius','archive'}
            expect(page.locator('#source-controls')).to_be_hidden()
            assert page.evaluate('Home.accepts(2,1)')==0
            report['checks'].append('Search submission and streamed response use real UI handlers, selected sources, mode and cover policy')
            page.locator('#query').fill('Deferred A');page.locator('#search-button').click();page.wait_for_timeout(100)
            page.locator('#query').fill('Deferred B');page.locator('#search-button').click();page.wait_for_timeout(100)
            assert len(deferred)==2
            assert 'cancelada' not in page.locator('#progress-label').text_content()
            deferred[1][0].fulfill(content_type='application/x-ndjson',body='\n'.join(json.dumps(e) for e in deferred[1][1])+'\n')
            expect(page.locator('#cancel')).to_be_hidden()
            deferred[0][0].fulfill(content_type='application/x-ndjson',body='\n'.join(json.dumps(e) for e in deferred[0][1])+'\n')
            expect(page.locator('#results-title')).to_contain_text('Deferred B')
            report['checks'].append('Aborting an old query cannot overwrite the new query progress')
            page.evaluate(fixtures['FIXTURE'],12)
            for width,height in [(1440,1000),(768,1024),(390,844),(320,800)]:
                page.set_viewport_size({'width':width,'height':height})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
                assert page.locator('.track-group').first.bounding_box()['y']<height
                page.screenshot(path=str(OUT/f'results-{width}.png'),full_page=True,animations='disabled')
            page.set_viewport_size({'width':1440,'height':1000})
            origin=page.locator('.origin>a').first;origin.focus()
            page.evaluate("tracks[0].album='Updated album';renderResults()")
            assert page.locator('.origin>a').first.evaluate('n=>n===document.activeElement')
            report['checks'].append('Results remain above fold and preserve focus while updating')
            files=page.locator('.origin button').first;files.click()
            expect(page.locator('#download-manifest')).to_be_visible()
            expect(page.locator('#download-options .audio-quality').first).to_contain_text('320 kbps')
            expect(page.locator('#download-options .audio-quality').first).to_contain_text('informado pela fonte')
            assert page.locator('#download-dialog').evaluate("n=>n.classList.contains('inline-downloads') && !!n.closest('.track-group') && !n.matches(':modal')")
            assert page.locator('.download-inspect').evaluate("n=>!n.closest('#download-dialog')")
            assert 'PDF excluído' not in page.locator('#download-options').inner_text()
            page.locator('#download-kind').select_option('artwork')
            expect(page.locator('.download-option')).to_have_count(1)
            expect(page.locator('.download-option-info')).to_contain_text('cover.jpg')
            page.locator('#download-kind').select_option('')
            expect(page.locator('#download-zip')).to_be_disabled()
            page.locator('.download-option-info').nth(0).click();page.locator('.download-option-info').nth(1).click()
            expect(page.locator('#download-zip')).to_be_enabled()
            page.locator('#download-close').click()
            files.click()
            assert page.locator('.download-option input:checked').count()==2
            page.locator('#download-zip').click()
            expect(page.locator('.download-job-actions button')).to_be_visible()
            assert preparations[-1]['option_ids']==['option_0','option_1'] and preparations[-1]['pack']=='zip'
            action=page.locator('.download-job-actions button');action.focus();page.wait_for_timeout(1200)
            assert action.evaluate('n=>n===document.activeElement')
            page.evaluate("tracks[0].year='2027';renderResults()")
            assert page.locator('#download-dialog').evaluate('n=>n.isConnected && n.open')
            assert page.locator('.download-job-actions button').evaluate('n=>n===document.activeElement')
            jobs[0]['status']='ready'
            jobs[0]['quality_files']=[{'filename':'song.flac','declared':{'sample_rate':44100},'measured':{'codec':'flac','sample_rate':96000,'bits_per_sample':24,'channels':2},'basis':'header'}]
            expect(page.locator('.download-save')).to_be_visible(timeout=4000)
            page.locator('.quality-details summary').click()
            expect(page.locator('.quality-details')).to_contain_text('24 bits')
            expect(page.locator('.quality-details')).to_contain_text('lido nos cabeçalhos')
            expect(page.locator('#download-job-status')).to_contain_text('Pronto para salvar')
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(OUT/'files-inline-390.png'),full_page=True)
            page.locator('#download-close').click();page.locator('#nav-downloads').click()
            assert page.locator('#download-dialog').evaluate("n=>n.matches(':modal') && !n.closest('.track-group')")
            expect(page.locator('.download-save')).to_be_visible()
            assert page.locator('.quality-details').evaluate('n=>n.open')
            page.keyboard.press('Escape')
            files.click()
            assert page.locator('.download-option input:checked').count()==2
            page.locator('#download-close').click()
            report['checks'].append('Inline files, preserved selection, exact ZIP IDs, stable queue, ready announcements and global Downloads')
            held=[];poll_calls=[]
            page.unroute('**/api/downloads/jobs')
            def delayed_poll(route):
                poll_calls.append(route)
                if len(poll_calls)==1:held.append(route)
                else:route.fulfill(json=[])
            page.route('**/api/downloads/jobs',delayed_poll)
            page.route('**/api/downloads/jobs/*',lambda route:route.fulfill(json={'cancelled':True}))
            page.locator('#nav-downloads').click();page.wait_for_timeout(100)
            page.locator('.download-job-actions button').click()
            expect(page.locator('#download-jobs')).to_contain_text('Nenhuma preparação')
            assert len(held)==1
            held[0].fulfill(json=jobs);page.wait_for_timeout(150)
            assert page.locator('.download-save').count()==0
            page.keyboard.press('Escape')
            report['checks'].append('Out-of-order queue responses cannot resurrect a removed preparation')
            page.locator('#nav-settings').click();page.locator('[data-panel="custom"]').click()
            expect(page.locator('.download-inspect')).to_be_visible()
            page.locator('#source-format').select_option('external')
            expect(page.locator('#source-method')).to_be_hidden()
            page.locator('#nav-search').click()
            page.set_viewport_size({'width':1440,'height':1000})
            page.evaluate("tracks[0].file_access='catalogue';tracks[0].audio_available=false;renderResults()")
            assert page.locator('[data-result-key="fixture-0"]').count()==0
            assert page.locator('.track-group').count()==11
            report['checks'].append('Settings/editor and manual inspection remain accessible; catalogue never offers a file action')
            page.locator('#query').fill('No audio');page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden()
            expect(page.locator('#result-count')).to_contain_text('0 resultados com áudio')
            page.locator('#source-notices summary').click()
            for text in ['nomes ou versões diferentes','sem áudio confirmado','falha ao verificar','sem concluir no prazo','conector de catálogo']:
                expect(page.locator('#source-notices-body')).to_contain_text(text)
            page.locator('#query').fill('Grouped');page.locator('#search-button').click()
            expect(page.locator('#cancel')).to_be_hidden()
            expect(page.locator('.track-group')).to_have_count(2)
            expect(page.locator('.track-group').first.locator('.origin')).to_have_count(2)
            expect(page.locator('.track-group').first).to_contain_text('Formatos listados: MP3')
            expect(page.locator('#result-count')).to_contain_text('2 resultados com áudio · 3 origens')
            report['checks'].append('Empty-search diagnostics distinguish names, missing audio, failed checks, timeouts and skipped catalogues; matching origins group without merging remixes')
            page.locator('#nav-settings').click();page.locator('[data-panel="preferences"]').click()
            page.locator('#pref-download-format').select_option('MP3');page.locator('#pref-download-pack').select_option('original');page.locator('#pref-download-images').check()
            page.locator('#settings-form button[type="submit"]').click()
            expect(page.locator('#save-status')).to_contain_text('Ajustes salvos')
            page.reload();page.wait_for_function("typeof window.showFiles==='function'")
            page.evaluate(fixtures['FIXTURE'],2)
            page.locator('.origin button').first.click()
            expect(page.locator('#download-manifest')).to_be_visible()
            expect(page.locator('#download-preference-note')).to_contain_text('MP3 não está disponível')
            assert page.locator('.download-option input:checked').count()==0
            expect(page.locator('#download-pack')).to_have_value('original')
            page.locator('#download-close').click();page.locator('#nav-settings').click()
            expect(page.locator('#pref-download-images')).to_be_checked()
            page.locator('#pref-download-format').select_option('FLAC');page.locator('#settings-form button[type="submit"]').click()
            expect(page.locator('#save-status')).to_contain_text('Ajustes salvos')
            page.reload();page.wait_for_function("typeof window.showFiles==='function'")
            page.evaluate(fixtures['FIXTURE'],2)
            page.locator('.origin button').first.click()
            expect(page.locator('#download-manifest')).to_be_visible()
            assert page.locator('.download-option input:checked').count()==9
            page.locator('#download-clear').click()
            for id in ['option_0','option_1','image_1']:page.locator('#download-file-'+id).check()
            page.unroute('**/api/downloads/jobs');page.route('**/api/downloads/jobs',lambda r:r.fulfill(json=jobs))
            before=len(preparations);page.locator('#download-zip').click()
            expect(page.locator('#download-preference-note')).to_contain_text('3/3 preparações criadas')
            assert [p['option_ids'] for p in preparations[before:]]==[['option_0'],['option_1'],['image_1']]
            assert all(p['pack']=='original' for p in preparations[before:])
            assert page.locator('.download-option input:checked').count()==0
            for id in ['option_0','option_1']:page.locator('#download-file-'+id).check()
            fail_option='option_1';page.locator('#download-zip').click()
            expect(page.locator('#download-error')).to_contain_text('1/2 preparações criadas')
            expect(page.locator('#download-file-option_0')).not_to_be_checked()
            expect(page.locator('#download-file-option_1')).to_be_checked()
            fail_option=None
            page.locator('#download-close').click()
            report['checks'].append('Saved download preferences survive reload, absent format never substitutes, audio/image preselection is reviewed and separate-file batches use exact IDs')
            coverage={'searches':10,'pages':1,'with_audio':4,'first_audio_ms':250,'source_mode_searches':2,'downloads':{'ready':2,'failed':1},'retention':500,'sources':[{'source':'archive','attempts':10,'with_audio':4,'cached':2,'statuses':{'success':4,'timeout':1,'empty':5},'diagnostics':{'no_audio':3},'downloads':{'ready':2,'failed':1}}]}
            page.route('**/api/coverage',lambda r:r.fulfill(json=coverage))
            page.locator('#nav-settings').click();page.locator('[data-panel="coverage"]').click()
            expect(page.locator('#coverage-summary')).to_contain_text('4/10 buscas com áudio')
            expect(page.locator('#coverage-sources')).to_contain_text('Internet Archive')
            assert page.locator('.coverage-table th').first.evaluate("n=>getComputedStyle(n).paddingTop")=='12px'
            page.locator('.coverage-sample summary').click()
            assert page.locator('#coverage-queries').evaluate("n=>getComputedStyle(n).display")=='block'
            page.locator('#coverage-queries').fill('Artist - Verified test title')
            page.locator('#coverage-run').click()
            expect(page.locator('#coverage-status')).to_contain_text('1/1 consultas concluídas')
            expect(page.locator('#coverage-results')).to_contain_text('1 origens com áudio confirmado')
            assert queries[-1]['mode']=='auto' and queries[-1]['require_audio'] is True
            for width,height in [(1440,1000),(390,844)]:
                page.set_viewport_size({'width':width,'height':height})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(OUT/f'coverage-{width}.png'),full_page=True)
            page.locator('#coverage-queries').fill('Deferred sample');page.locator('#coverage-run').click()
            expect(page.locator('#coverage-cancel')).to_be_visible()
            page.locator('#coverage-cancel').click()
            expect(page.locator('#coverage-status')).to_contain_text('Teste cancelado')
            # Finish the held browser fixture; the cancelled request must not change its report.
            deferred[-1][0].fulfill(content_type='application/x-ndjson',body='\n'.join(json.dumps(e) for e in deferred[-1][1])+'\n')
            expect(page.locator('#coverage-status')).to_contain_text('0/1 consultas concluídas')
            report['checks'].append('Coverage table, editable sample list and cancellation work without overflow on desktop/mobile')
            with page.expect_popup() as license_popup:
                page.locator('footer a[href="/static/licenses.html"]').click()
            licenses=license_popup.value
            expect(licenses.locator('h1')).to_have_text('Licenças e instruções')
            expect(licenses.locator('body')).to_contain_text('MIT License')
            assert licenses.locator('script').count()==0
            licenses.close()
            report['checks'].append('Embedded license/instruction page opens from footer without a separate ZIP')
            assert not report['errors'],report['errors']
            browser.close()
    finally:
        (OUT/'checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        if base:
            try:
                request=urllib.request.Request(base+'/api/shutdown',data=b'{}',headers={'Content-Type':'application/json','X-EveryTune':'1'},method='POST');urllib.request.urlopen(request,timeout=2).close();process.wait(timeout=10)
            except Exception:process.terminate()
        else:process.terminate()
print(json.dumps(report,ensure_ascii=False,indent=2))
