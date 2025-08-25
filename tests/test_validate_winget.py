
import subprocess
import sys
from pathlib import Path

import yaml
from scripts import release

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_winget_malformed(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ invalid json }", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_winget.py"), str(bad_json)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "Failed to parse" in result.stderr


def test_validate_winget_success(tmp_path: Path) -> None:
    valid_json = tmp_path / "good.json"
    valid_json.write_text(
        '{"Sources": [{"Packages": ["foo"]}]}',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_winget.py"), str(valid_json)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0


def test_release_updates_manifest(tmp_path: Path, monkeypatch) -> None:
    manifest_src = REPO_ROOT / "winget" / "tino.yaml"
    manifest_dest = tmp_path / "winget" / "tino.yaml"
    manifest_dest.parent.mkdir()
    manifest_dest.write_text(manifest_src.read_text(), encoding="utf-8")
    monkeypatch.setattr(release, "REPO", tmp_path)
    tag = "v1.2.3"
    version = "1.2.3"
    sha = "f" * 64
    release.update_winget(tag, version, sha)
    data = yaml.safe_load(manifest_dest.read_text())
    assert data["PackageVersion"] == version
    assert data["Installers"][0]["Sha256"] == sha
    assert data["Installers"][0]["InstallerUrl"].endswith(
        f"/download/{tag}/tino-windows-{version}.zip"
    )

