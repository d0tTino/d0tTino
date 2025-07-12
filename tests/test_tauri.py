import subprocess
import shutil
from pathlib import Path

import pytest


def _has_tauri_deps() -> bool:
    """Return True if required system dependencies are available."""
    if shutil.which("cargo") is None or shutil.which("pkg-config") is None:
        return False
    try:
        subprocess.run(
            ["pkg-config", "--exists", "javascriptcoregtk-4.0"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


@pytest.mark.skipif(not _has_tauri_deps(), reason="missing Tauri system dependencies")
def test_tauri_build_release() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = repo_root / "src-tauri" / "Cargo.toml"
    result = subprocess.run(
        ["cargo", "test", "--manifest-path", str(manifest), "--release"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0

