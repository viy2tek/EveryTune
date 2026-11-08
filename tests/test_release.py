import hashlib
from pathlib import Path
import tomllib
from types import SimpleNamespace
import zipfile

import pytest

from everytune import __version__
from scripts import package_release as release


def test_release_version_matches_app():
    assert tomllib.loads((release.ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']==__version__


def test_dependency_notices_follow_active_dependencies_and_keep_original_bytes(tmp_path,monkeypatch):
    text=b'Original license notice\n'
    license_path=tmp_path/'LICENSE';license_path.write_bytes(text)
    seen=[]
    def distribution(name):
        seen.append(name)
        return SimpleNamespace(requires=['child; python_version >= "3.12"','ignored; extra == "unused"'] if name=='root' else [],
            files=[Path('LICENSE')],locate_file=lambda p:license_path)
    monkeypatch.setattr(release.metadata,'distribution',distribution)
    notices=release.dependency_licenses(['root'])
    assert set(seen)=={'root','child'}
    assert set(notices.values())=={text}
    monkeypatch.setattr(release.metadata,'distribution',lambda n:SimpleNamespace(requires=[],files=[]))
    with pytest.raises(ValueError,match='No license'):release.dependency_licenses(['missing'])


def test_release_zip_and_checksum_only_include_explicit_files(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir();(root/'docs').mkdir()
    for name in ['LICENSE','CHANGELOG.md','THIRD_PARTY_NOTICES.md','docs/RELEASE_USER_GUIDE.txt']:(root/name).write_text(name,encoding='utf-8')
    (root/'pyproject.toml').write_text('[project]\nversion="0.4.0b1"\n')
    (root/'requirements.txt').write_text('fastapi==0.162.0\n')
    (root/'private.env').write_text('DO NOT SHIP')
    (tmp_path/'LICENSE.txt').write_text('Python notice')
    executable=root/'EveryTune.exe';executable.write_bytes(b'fixture executable')
    monkeypatch.setattr(release,'ROOT',root);monkeypatch.setattr(release.sys,'base_prefix',str(tmp_path))
    monkeypatch.setattr(release,'dependency_licenses',lambda names:{'third-party/test/LICENSE':b'Dependency notice'})
    path=release.package(executable,tmp_path/'out')
    assert path.name=='EveryTune-v0.4.0-beta.1-windows-x64.zip'
    with zipfile.ZipFile(path) as bundle:
        assert bundle.read('EveryTune.exe')==b'fixture executable'
        assert 'private.env' not in bundle.namelist()
        assert {'LICENSE','third-party/Python/LICENSE.txt','third-party/test/LICENSE'}<=set(bundle.namelist())
        assert bundle.testzip() is None
    assert (path.parent/'SHA256SUMS.txt').read_text().split()[0]==hashlib.sha256(path.read_bytes()).hexdigest()
    direct=path.with_suffix('.exe')
    assert direct.read_bytes()==executable.read_bytes()
    sums=(path.parent/'SHA256SUMS.txt').read_text().splitlines()
    assert len(sums)==2 and sums[1]==f'{hashlib.sha256(direct.read_bytes()).hexdigest()}  {direct.name}'


def test_embedded_license_notices_escape_text_and_preserve_contents():
    fragment=release.license_fragment({'LICENSE':b'MIT notice\nCopyright example',
        'third-party/<example>/LICENSE':b'<script>not executable</script> & text'})
    assert '<script>' not in fragment and '&lt;script&gt;not executable&lt;/script&gt; &amp; text' in fragment
    assert 'MIT notice\nCopyright example' in fragment and '&lt;example&gt;' in fragment
