import os
import subprocess
import shutil
from pathlib import Path
from unittest import mock
import re
import sys
import pytest

SCRIPT = Path('scripts/fix-path.ps1')

def run_fix_path():
    pwsh = shutil.which('pwsh')
    if pwsh:
        subprocess.run([pwsh, '-NoLogo', '-NoProfile', '-File', str(SCRIPT)], check=True)
    else:
        subprocess.run([
            'powershell',
            '-NoLogo',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', str(SCRIPT)
        ], check=True)


def run_fix_path_capture(env, *, capture_stderr: bool = False):
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        pytest.skip("PowerShell not available")
    command = f"& '{SCRIPT}' ; [Environment]::GetEnvironmentVariable('Path','User')"
    result = subprocess.run(
        [pwsh, "-NoLogo", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    output = lines[-1] if lines else ""
    if capture_stderr:
        return output, result.stderr
    return output




def test_run_fix_path_uses_pwsh_if_available(monkeypatch):
    mock_run = mock.Mock()
    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr(shutil, 'which', lambda cmd: '/usr/bin/pwsh' if cmd == 'pwsh' else None)
    run_fix_path()
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert 'pwsh' in args[0]
    assert args[-1].endswith('fix-path.ps1')


def test_run_fix_path_falls_back_to_powershell(monkeypatch):
    mock_run = mock.Mock()
    monkeypatch.setattr(subprocess, 'run', mock_run)
    monkeypatch.setattr(shutil, 'which', lambda cmd: None)
    run_fix_path()
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == 'powershell'
    assert args[-1].endswith('fix-path.ps1')

def test_fix_path_script_content():
    text = SCRIPT.read_text(encoding='utf-8')
    assert "SetEnvironmentVariable('Path'" in text
    assert '.ToLower()' in text


def _dedupe_paths(paths):
    unique = []
    seen = set()
    for p in paths:
        trimmed = p.strip()
        collapsed = re.sub(r'[\\/]+', r'\\', trimmed).rstrip('\\/')
        lower = collapsed.lower()
        if collapsed and lower not in seen:
            unique.append(collapsed)
            seen.add(lower)
    return unique


def test_dedupe_trailing_slashes():
    paths = [r'C:\Tools', r'C:\Tools\\']
    assert _dedupe_paths(paths) == [r'C:\Tools']


def test_case_insensitive_after_trimming():
    paths = [r'C:\Tools\\', r'c:\tools']
    assert _dedupe_paths(paths) == [r'C:\Tools']


@pytest.mark.skipif(sys.platform != 'win32', reason='requires Windows PATH mechanics')
def test_fix_path_script_deduplicates(tmp_path):
    env = os.environ.copy()
    env.update({
        'Path': r'C:\Tools;C:\Tools\\;c:\tools;C:\Other\\;C:\Other',
        'USERPROFILE': str(tmp_path),
    })
    expected = r'C:\Tools;C:\Other;' + str(Path(tmp_path) / 'bin')
    output = run_fix_path_capture(env)
    assert output == expected


@pytest.mark.skipif(not shutil.which("pwsh") and not shutil.which("powershell"), reason="PowerShell not available")
def test_fix_path_warns_and_truncates(tmp_path):
    paths = [fr"C:\\Path{i}" for i in range(300)]
    long_path = ";".join(paths)
    assert len(long_path) > 1023
    env = os.environ.copy()
    env.update({
        "Path": long_path,
        "USERPROFILE": str(tmp_path),
    })
    output, stderr = run_fix_path_capture(env, capture_stderr=True)
    assert len(output) == 1023
    assert output == long_path[:1023]
    assert "PATH length exceeds 1023 characters" in stderr
    assert "Some PATH entries were dropped" in stderr
