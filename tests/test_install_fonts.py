import os
import subprocess
from pathlib import Path


def _run_script(env):
    script = Path(__file__).resolve().parents[1] / "scripts" / "helpers" / "install_fonts.sh"
    return subprocess.run([
        "/bin/bash",
        str(script)
    ], env=env, capture_output=True, text=True)


def test_missing_curl(tmp_path):
    env = os.environ.copy()
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    (stub_bin / "bash").symlink_to("/bin/bash")
    (stub_bin / "uname").write_text("#!/usr/bin/env bash\necho Linux\n")
    (stub_bin / "uname").chmod(0o755)
    env["PATH"] = str(stub_bin)
    result = _run_script(env)
    assert result.returncode
    assert "curl is required" in result.stderr


def test_missing_unzip(tmp_path):
    env = os.environ.copy()
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    # provide curl but not unzip
    (stub_bin / "bash").symlink_to("/bin/bash")
    (stub_bin / "curl").symlink_to("/usr/bin/curl")
    (stub_bin / "uname").write_text("#!/usr/bin/env bash\necho Linux\n")
    (stub_bin / "uname").chmod(0o755)
    env["PATH"] = str(stub_bin)
    result = _run_script(env)
    assert result.returncode
    assert "unzip is required" in result.stderr
