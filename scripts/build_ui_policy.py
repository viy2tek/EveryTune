"""Check Bend proofs and emit the editor policy actually shipped to browsers."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    launcher = shutil.which('bend')
    if not launcher and sys.platform == 'win32':
        candidate = Path.home() / '.bend/bin/bend.cmd'
        if candidate.is_file():
            launcher = str(candidate)
    if not launcher:
        raise SystemExit('Bend is required to rebuild ui-policy.mjs; end users do not need it.')
    proof = subprocess.run([launcher, 'PROOF.bend'], cwd=ROOT, text=True, capture_output=True)
    print(proof.stdout, end='')
    if proof.returncode or 'ALL PROOFS CHECK' not in proof.stdout:
        raise SystemExit(proof.stderr or 'Bend proofs did not pass.')
    for source,target in [('ui_policy.bend','ui-policy.mjs'),('ui/home/main.bend','home.mjs')]:
        output=ROOT/'everytune/static'/target
        temporary=output.with_suffix('.new.mjs')
        result=subprocess.run([launcher,source,'-o',temporary.relative_to(ROOT).as_posix()],cwd=ROOT,text=True,capture_output=True)
        if result.returncode or 'SOME PROOFS FAIL' in result.stdout or result.stderr.strip() or not temporary.is_file():
            raise SystemExit(result.stdout+result.stderr or 'Bend emission failed')
        temporary.replace(output)
    subprocess.run(['node','--input-type=module','-e', '''
import fs from 'node:fs';
import home from './everytune/static/home.mjs';
const path='everytune/static/index.html';
const html=fs.readFileSync(path,'utf8');
if (!html.includes('<!-- HOME:START -->') || !html.includes('<!-- HOME:END -->')) throw Error('Missing home build markers');
fs.writeFileSync(path,html.replace(/<!-- HOME:START -->[\\s\\S]*?<!-- HOME:END -->/,'<!-- HOME:START -->\\n'+home.markup()+'\\n<!-- HOME:END -->'));
let updated=fs.readFileSync(path,'utf8');
for(const [marker,markup] of [['DOWNLOAD-PREFERENCES',home.download_preferences_markup()],['COVERAGE',home.coverage_markup()],['DOWNLOAD-SELECTION',home.selection_markup()],['FOOTER',home.footer_markup()]]) {
  const start='<!-- '+marker+':START -->',end='<!-- '+marker+':END -->';
  if(!updated.includes(start) || !updated.includes(end)) throw Error('Missing workflow markers: '+marker);
  const first=updated.indexOf(start),last=updated.indexOf(end,first);
  updated=updated.slice(0,first)+start+'\\n'+markup+'\\n'+updated.slice(last);
}
fs.writeFileSync(path,updated);
fs.writeFileSync('everytune/static/home.css',home.css());
'''],cwd=ROOT,check=True)


if __name__ == '__main__':
    main()
