"""Build a native executable using the current Python environment."""
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

root = Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--distpath',type=Path,default=root/'dist')
args=parser.parse_args()
subprocess.run([sys.executable,str(root / 'scripts' / 'build_ui_policy.py')],cwd=root,check=True)
data = root / "everytune" / "data"
data.mkdir(exist_ok=True)
for name in ("source-audit.json","free-websites-audit.json"):
    if (root / "docs" / name).exists():
        shutil.copyfile(root / "docs" / name,data / name)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console",
                "--name", "EveryTune", "--distpath",str(args.distpath.resolve()), "--add-data", f"{root / 'everytune' / 'static'}:everytune/static",
                "--add-data",f"{data}:everytune/data",
                "--collect-submodules", "uvicorn", str(root / "run.py")], cwd=root, check=True)
