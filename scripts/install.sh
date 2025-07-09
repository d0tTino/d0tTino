#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${OSTYPE:-}" ]]; then
    OSTYPE="$(uname -s | tr '[:upper:]' '[:lower:]')"
    case $OSTYPE in
        mingw*) OSTYPE="msys" ;;
    esac
fi

run_pwsh() {
    pwsh -NoLogo -NoProfile -File "$script_dir/$1"
}

if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    run_pwsh helpers/install_fonts.ps1
    run_pwsh helpers/sync_palettes.ps1
    run_pwsh setup-hooks.ps1
else
    bash "$script_dir/helpers/install_fonts.sh"
    bash "$script_dir/helpers/sync_palettes.sh"
    bash "$script_dir/setup-hooks.sh"
fi
