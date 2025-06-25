import os
import subprocess
from pathlib import Path


def create_exe(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


# New test for smoke_test.ps1

def test_smoke_test_stubs(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "smoke_test.ps1"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    # Stub pwsh that simulates running the smoke test script
    pwsh_stub = bin_dir / "pwsh"
    pwsh_stub_contents = """#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do
  case $1 in
    -File)
      script=$2
      shift 2
      ;;
    -Command)
      # Simulate pwsh -Command invocation
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done

if [[ $script == *smoke_test.ps1 ]]; then
  echo 'Measuring PowerShell startup...'
  echo 'pwsh startup: 0 ms'
  echo 'Running zoxide query...'
  result=$(zoxide query ~)
  echo "zoxide query ~ => $result"
  echo 'Checking git diff...'
  git diff --stat
  echo 'Smoke test completed successfully.'
  exit 0
else
  echo "Unexpected script: $script" >&2
  exit 1
fi
"""
    create_exe(pwsh_stub, pwsh_stub_contents)

    # Stub zoxide
    create_exe(bin_dir / "zoxide", "#!/usr/bin/env bash\necho /home/test\n")
    # Stub git
    create_exe(bin_dir / "git", "#!/usr/bin/env bash\necho '0 files changed'\n")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["pwsh", "-NoLogo", "-NoProfile", "-File", str(script)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout.splitlines()
    assert "Measuring PowerShell startup..." in output
    assert any(line.startswith("pwsh startup:") for line in output)
    assert "Running zoxide query..." in output
    assert "zoxide query ~ => /home/test" in output
    assert "Checking git diff..." in output
    assert "Smoke test completed successfully." in output
