"""Exercise the emitted Bend implementation through its real JavaScript bridge."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_emitted_editor_policy():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node required to exercise the browser policy')
    root = Path(__file__).resolve().parent.parent
    subprocess.run([node, '--input-type=module', '-e', '''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import policy from './everytune/static/ui-policy.mjs';
import home from './everytune/static/home.mjs';
for (const count of [0,1,2,100,4294967295]) assert.equal(home.can_zip(count),Number(count>0));
for (const ref of [0,1]) assert.equal(home.file_action(1,ref),0);
for (const phase of [0,1,2,3,4,5,6,7,8,99]) assert.equal(home.can_save(phase),Number(phase===7));
for (const id of [0,1,1000,4294967295]) {
  assert.equal(home.accepts(id,id),1);
  assert.equal(home.accepts(id,(id+1)>>>0),0);
}
assert.equal(home.transition(2,1),1);
assert.equal(home.transition(2,99),2);
assert.match(home.markup(),/options-toggle/);
assert.ok(!home.markup().includes('Todos os caminhos'));
assert.match(home.css(),/body.home/);
assert.equal(home.css().split('{').length,home.css().split('}').length);
assert.equal(home.toggle(0),1);assert.equal(home.toggle(1),0);
assert.equal(home.audio_result(0),0);assert.equal(home.audio_result(1),1);
assert.equal(home.quality('MP3',320000,44100,0,2,0),'MP3 · 320 kbps · 44100 Hz · estéreo · informado pela fonte');
assert.equal(home.quality('FLAC',0,96000,24,2,1),'FLAC · 96000 Hz · 24 bits · estéreo · lido no arquivo');
for(const kind of [0,1,2,3,99]) assert.equal(home.allowed_file(kind),Number(kind===1 || kind===2));
for(const kind of [0,1,2,3,99]) for(const direct of [0,1]) for(const preferred of [0,1]) for(const images of [0,1]) {
  assert.equal(home.select_file(kind,direct,preferred,images),Number(direct===1 && (kind===1 && preferred===1 || kind===2 && images===1)));
}
const html=fs.readFileSync('everytune/static/index.html','utf8');
assert.equal(html.split('<!-- HOME:START -->')[1].split('<!-- HOME:END -->')[0].trim(),home.markup().trim());
assert.equal(fs.readFileSync('everytune/static/home.css','utf8'),home.css());
for(const [marker,markup] of [['DOWNLOAD-PREFERENCES',home.download_preferences_markup()],['COVERAGE',home.coverage_markup()],['DOWNLOAD-SELECTION',home.selection_markup()]]) {
  assert.equal(html.split('<!-- '+marker+':START -->')[1].split('<!-- '+marker+':END -->')[0].trim(),markup.trim());
}
for (const format of [0,1,2,3,99,4294967295]) {
  const integrated=format===1 || format===2;
  assert.equal(policy.mapping(format),Number(integrated));
  for (const enabled of [0,1]) {
    assert.equal(policy.post_body(format,enabled),integrated ? enabled : 0);
    assert.equal(policy.auth_name(format,enabled),integrated ? enabled : 0);
  }
}
'''], cwd=root, check=True, capture_output=True, text=True)
