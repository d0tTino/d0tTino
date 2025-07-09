#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts="$repo_root/scripts"

# Determine the platform when OSTYPE is not provided
if [[ -z "${OSTYPE:-}" ]]; then
    OSTYPE="$(uname -s | tr '[:upper:]' '[:lower:]')"
    case $OSTYPE in
        mingw*) OSTYPE="msys" ;;
    esac
fi

install_winget=false
install_windows_terminal=false
install_wsl=false
setup_wsl=false
setup_docker=false
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

run_pwsh() {
    local script=$1
    shift
    pwsh -NoLogo -NoProfile -File "$scripts/$script" "$@"
}


if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    run_pwsh fix-path.ps1
    run_pwsh helpers/install_common.ps1
else
    bash "$scripts/install_common.sh"
fi

if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    if $install_winget; then run_pwsh setup-winget.ps1; fi
    if $install_windows_terminal; then run_pwsh install-windows-terminal.ps1; fi
    if $install_wsl; then run_pwsh install-wsl.ps1; fi
    if $setup_wsl; then run_pwsh setup-wsl.ps1; fi
    if $setup_docker; then
        args=()
        [[ -n $docker_image ]] && args+=("-ImageName" "$docker_image")
        run_pwsh setup-docker.ps1 "${args[@]}"
    fi
else
    if $setup_wsl; then bash "$scripts/setup-wsl.sh"; fi
    if $setup_docker; then
        args=()
        [[ -n $docker_image ]] && args+=("--image" "$docker_image")
        bash "$scripts/setup-docker.sh" "${args[@]}"
    fi
fi
