#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scripts="$repo_root/scripts"

# Determine the platform when OSTYPE is not provided
if [[ -z "${OSTYPE:-}" ]]; then
    OSTYPE="$(uname -s)"
fi

# Normalize Windows variants and lower-case the final value
case $OSTYPE in
    CYGWIN*|cygwin*) OSTYPE="cygwin" ;;
    MINGW*|mingw*|MSYS*|msys*) OSTYPE="msys" ;;
    Windows_NT*) OSTYPE="windows" ;;
esac

OSTYPE="${OSTYPE,,}"

ensure_deps() {
    local missing=()
    for cmd in "$@"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        if [[ $OSTYPE == darwin* ]]; then
            if command -v brew >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with Homebrew" >&2
                brew install "${missing[@]}"
            else
                echo "Missing ${missing[*]}" >&2
                echo "Install Homebrew from https://brew.sh and run: brew install ${missing[*]}" >&2
                exit 1
            fi
        elif [[ $OSTYPE == linux* ]]; then
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with apt-get" >&2
                sudo apt-get update
                sudo apt-get install -y "${missing[@]}"
            elif command -v dnf >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with dnf" >&2
                sudo dnf install -y "${missing[@]}"
            elif command -v pacman >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with pacman" >&2
                sudo pacman -S --noconfirm "${missing[@]}"
            else
                echo "Missing ${missing[*]}. Please install them and re-run this script." >&2
                exit 1
            fi
        else
            echo "Missing ${missing[*]}. Please install them and re-run this script." >&2
            exit 1
        fi
    fi
}

run_pwsh() {
    local script=$1
    shift
    pwsh -NoLogo -NoProfile -File "$scripts/$script" "$@"
}

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
            ;;
    esac
    shift
done

# Ensure core utilities are available
ensure_deps curl unzip git

if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    run_pwsh fix-path.ps1
    run_pwsh helpers/install_common.ps1
else
    bash "$scripts/setup-hooks.sh"
    bash "$scripts/helpers/install_fonts.sh"
    bash "$scripts/helpers/sync_palettes.sh"
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
