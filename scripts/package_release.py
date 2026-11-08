"""Package an already verified Windows build; never upload or modify user data."""
import argparse
import hashlib
from importlib import metadata
from pathlib import Path
import re
import sys
import tomllib
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT=Path(__file__).resolve().parent.parent


def dependency_licenses(names):
    files={};seen=set();pending=list(names)
    while pending:
        name=canonicalize_name(pending.pop())
        if name in seen:continue
        seen.add(name);dist=metadata.distribution(name)
        for value in dist.requires or []:
            requirement=Requirement(value)
            if requirement.marker is None or requirement.marker.evaluate({'extra':''}):pending.append(requirement.name)
        found=0
        for path in dist.files or []:
            if not re.match(r'^(licen[cs]e|copying|notice|authors)([.\-_].*)?$',Path(path).name,re.I):continue
            full=Path(dist.locate_file(path))
            if not full.is_file():continue
            files[f'third-party/{name}/{path.as_posix()}']=full.read_bytes();found+=1
        if not found:raise ValueError(f'No license notice found for {name}; inspect its distribution before publishing.')
    return files


def package(executable, output):
    if not executable.is_file():raise ValueError('Build the executable before packaging.')
    version=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    tag=re.sub(r'b(\d+)$',r'-beta.\1',version)
    docs={name:(ROOT/name).read_bytes() for name in ['LICENSE','CHANGELOG.md','THIRD_PARTY_NOTICES.md']}
    docs['LEIA-ME.txt']=(ROOT/'docs/RELEASE_USER_GUIDE.txt').read_bytes()
    names=[Requirement(line).name for line in (ROOT/'requirements.txt').read_text().splitlines() if line.strip() and not line.startswith('#')]
    docs.update(dependency_licenses(names+['pyinstaller']))
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.is_file():raise ValueError('Python LICENSE.txt is required in the Windows distribution.')
    docs['third-party/Python/LICENSE.txt']=python_license.read_bytes()
    output.mkdir(parents=True,exist_ok=True)
    archive=output/f'EveryTune-v{tag}-windows-x64.zip'
    temporary=archive.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.write(executable,'EveryTune.exe')
            for name,data in sorted(docs.items()):bundle.writestr(name,data)
        temporary.replace(archive)
    finally:temporary.unlink(missing_ok=True)
    with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n',encoding='utf-8')
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--executable',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'dist/releases');args=parser.parse_args()
    print(package(args.executable.resolve(),args.output.resolve()))
