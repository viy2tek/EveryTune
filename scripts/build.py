"""Build a native executable using the current Python environment."""
import subprocess
import sys
import shutil
import argparse
from pathlib import Path
from package_release import license_fragment,release_documents

root = Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--distpath',type=Path,default=root/'dist')
args=parser.parse_args()
subprocess.run([sys.executable,str(root / 'scripts' / 'build_ui_policy.py')],cwd=root,check=True)
fragment=root/'build/legal-notices.html';fragment.parent.mkdir(exist_ok=True)
fragment.write_text(license_fragment(release_documents()),encoding='utf-8')
subprocess.run(['node','--input-type=module','-e',
    "import fs from 'node:fs';import home from './everytune/static/home.mjs';fs.writeFileSync('everytune/static/licenses.html',home.license_page(fs.readFileSync(process.argv[1],'utf8')));",
    str(fragment)],cwd=root,check=True)
data = root / "everytune" / "data"
data.mkdir(exist_ok=True)
for name in ("source-audit.json","free-websites-audit.json"):
    if (root / "docs" / name).exists():
        shutil.copyfile(root / "docs" / name,data / name)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console",
                "--name", "EveryTune", "--distpath",str(args.distpath.resolve()), "--add-data", f"{root / 'everytune' / 'static'}:everytune/static",
                "--add-data",f"{data}:everytune/data",
                "--collect-submodules", "uvicorn", str(root / "run.py")], cwd=root, check=True)
