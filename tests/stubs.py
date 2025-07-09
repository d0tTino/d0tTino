from pathlib import Path


def create_stub_pwsh(path: Path, log: Path | None = None) -> None:
    """Create a PowerShell stub that logs invoked script names."""
    if log is None:
        log = path.parent / "pwsh.log"
    path.write_text(
        f"""#!/usr/bin/env bash
log_file='{log}'
file=""
args=()
while [[ $# -gt 0 ]]; do
  if [[ $1 == -File ]]; then
    file=$2
    shift 2
  else
    args+=($1)
    shift
  fi
done
root=$(dirname "$file")
base=$(basename "$file")
is_windows="${{STUB_IS_WINDOWS:-1}}"
if [[ $base == bootstrap.ps1 ]]; then
  install_winget=false
  install_windows_terminal=false
  install_wsl=false
  setup_wsl=false
  setup_docker=false
  for arg in "${{args[@]}}"; do
    case $arg in
      -InstallWinget) install_winget=true ;;
      -InstallWindowsTerminal) install_windows_terminal=true ;;
      -InstallWSL) install_wsl=true ;;
      -SetupWSL) setup_wsl=true ;;
      -SetupDocker) setup_docker=true ;;
    esac
  done
  echo fix-path.ps1 >> "$log_file"
  echo install_common.sh >> "$log_file"
  if [[ -f "$root/scripts/install_common.sh" ]]; then
    /bin/bash "$root/scripts/install_common.sh"
  fi
  if [[ $is_windows == 1 ]]; then
    $install_winget && echo setup-winget.ps1 >> "$log_file"
    $install_windows_terminal && echo install-windows-terminal.ps1 >> "$log_file"
    $install_wsl && echo install-wsl.ps1 >> "$log_file"
    $setup_wsl && echo setup-wsl.ps1 >> "$log_file"
    $setup_docker && echo setup-docker.ps1 >> "$log_file"
  else
    if [[ $setup_wsl == true ]]; then echo setup-wsl.sh >> "$log_file"; fi
    if [[ $setup_docker == true ]]; then echo setup-docker.sh >> "$log_file"; fi
  fi
  exit 0
else
  echo "$base" >> "$log_file"
  exit 0
fi
""",
        encoding="utf-8",
    )
    path.chmod(0o755)

def create_stub_install_common(path: Path, log: Path) -> None:
    """Create an install_common.sh stub along with helper stubs."""
    helpers = path.parent / "helpers"
    helpers.mkdir(exist_ok=True)
    (helpers / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\nif [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then\n  echo install_fonts_windows >> '{log}'\nelse\n  echo install_fonts_unix >> '{log}'\nfi\n",
        encoding="utf-8",
    )
    (helpers / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho pull_palettes >> '{log}'\n",
        encoding="utf-8",
    )
    (helpers / "install_fonts.ps1").write_text(
        f"#!/usr/bin/env bash\necho install_fonts_windows >> '{log}'\n",
        encoding="utf-8",
    )
    (helpers / "sync_palettes.ps1").write_text(
        f"#!/usr/bin/env bash\necho pull_palettes >> '{log}'\n",
        encoding="utf-8",
    )
    for f in helpers.iterdir():
        f.chmod(0o755)
    path.write_text(
        f"#!/usr/bin/env bash\necho install_common >> '{log}'\nbash \"$(dirname \"${{BASH_SOURCE[0]}}\")/setup-hooks.sh\"\nbash \"$(dirname \"${{BASH_SOURCE[0]}}\")/helpers/install_fonts.sh\"\nbash \"$(dirname \"${{BASH_SOURCE[0]}}\")/helpers/sync_palettes.sh\"\n",
        encoding="utf-8",
    )
    path.chmod(0o755)



def create_stub_install(path: Path, log: Path) -> None:
    """Create an install.sh stub that simulates font installation."""
    path.write_text(
        f"""#!/usr/bin/env bash
if [[ $OSTYPE == darwin* ]]; then
  echo install_fonts_unix >> '{log}'
elif [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
  echo install_fonts_windows >> '{log}'
else
  echo install_fonts_unix >> '{log}'
fi
echo pull_palettes >> '{log}'
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
