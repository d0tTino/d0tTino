#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts="$repo_root/scripts"


install_winget=false
install_windows_terminal=false
install_wsl=false
setup_wsl=false
setup_docker=false
dry_run=false
docker_image=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --winget)
            install_winget=true
            ;;
        --windows-terminal)
            install_windows_terminal=true
            ;;
        --install-wsl)
            install_wsl=true
            ;;
        --setup-wsl)
            setup_wsl=true
            ;;
        --setup-docker)
            setup_docker=true
            ;;
        --dry-run)
            dry_run=true
            ;;
        --image)
            docker_image=$2
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

args=( )
if $install_winget; then args+=(--winget); fi
if $install_windows_terminal; then args+=(--windows-terminal); fi
if $install_wsl; then args+=(--install-wsl); fi
if $setup_wsl; then args+=(--setup-wsl); fi
if $setup_docker; then args+=(--setup-docker); fi
if [[ -n $docker_image ]]; then args+=(--image "$docker_image"); fi
if $dry_run; then args+=(--dry-run); fi

if [[ ${OSTYPE:-} == msys* || ${OSTYPE:-} == cygwin* || ${OSTYPE:-} == win32* || ${OSTYPE:-} == windows* ]] && command -v pwsh >/dev/null 2>&1; then
    cmd=(pwsh -NoLogo -NoProfile -File "$scripts/helpers/install_common.ps1" "${args[@]}")
else
    cmd=(bash "$scripts/install_common.sh" "${args[@]}")
fi

if $dry_run; then
    echo "Dry run: ${cmd[*]}"
    "${cmd[@]}"
else
    "${cmd[@]}"
    if command -v pre-commit >/dev/null 2>&1; then
        hooks_path=$(git config --get core.hooksPath || true)
        if [[ -z "$hooks_path" || "$hooks_path" == ".git/hooks" ]]; then
            pre-commit install
        else
            pre-commit install --install-hooks || true
        fi
    else
        echo "pre-commit not found; skipping hook installation" >&2
    fi
fi
