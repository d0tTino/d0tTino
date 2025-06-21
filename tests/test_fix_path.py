import subprocess
import shutil
from pathlib import Path
from unittest import mock

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
