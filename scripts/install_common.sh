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

run_cmd() {
    if $dry_run; then
        echo "$*"
    else
        "$@"
    fi
}

ensure_deps() {
    local missing=()
    for cmd in "$@"; do
        if [[ $cmd == "neovim" ]]; then
            if ! command -v nvim >/dev/null 2>&1; then
                missing+=("$cmd")
            fi
            continue
        fi

        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        if [[ $OSTYPE == darwin* ]]; then
            if command -v brew >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with Homebrew" >&2
                run_cmd brew install "${missing[@]}"
            else
                echo "Missing ${missing[*]}" >&2
                echo "Install Homebrew from https://brew.sh and run: brew install ${missing[*]}" >&2
                exit 1
            fi
        elif [[ $OSTYPE == linux* ]]; then
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with apt-get" >&2
                run_cmd sudo apt-get update
                run_cmd sudo apt-get install -y "${missing[@]}"
            elif command -v dnf >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with dnf" >&2
                run_cmd sudo dnf install -y "${missing[@]}"
            elif command -v pacman >/dev/null 2>&1; then
                echo "Installing ${missing[*]} with pacman" >&2
                run_cmd sudo pacman -S --noconfirm "${missing[@]}"
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

install_terminal_emulator() {
    if [[ ! -f "$scripts/setup-ghostty.sh" ]]; then
        return
    fi

    case $OSTYPE in
        darwin*|linux*)
            run_cmd bash "$scripts/setup-ghostty.sh"
            ;;
        msys*|cygwin*|win32*|windows*)
            echo "Skipping Ghostty install on Windows; use Windows Terminal setup options instead."
            ;;
        *)
            echo "Skipping terminal emulator install for unsupported platform: $OSTYPE"
            ;;
    esac
}

run_pwsh() {
    local script=$1
    shift
    if $dry_run; then
        echo pwsh -NoLogo -NoProfile -File "$scripts/$script" "$@"
    else
        pwsh -NoLogo -NoProfile -File "$scripts/$script" "$@"
    fi
}

plugin_root="$HOME/.local/share/zsh/plugins"
autosuggest_repo="https://github.com/zsh-users/zsh-autosuggestions"
syntax_highlight_repo="https://github.com/zsh-users/zsh-syntax-highlighting"

clone_plugin_if_missing() {
    local repo_url=$1
    local destination=$2
    if [[ -d "$destination/.git" ]]; then
        echo "Plugin already installed at $destination"
        return
    fi
    if [[ -e "$destination" ]]; then
        echo "Skipping $destination because it exists and is not a git checkout" >&2
        return
    fi

    run_cmd mkdir -p "$(dirname "$destination")"
    run_cmd git clone "$repo_url" "$destination"
}

prompt_set_default_shell() {
    local zsh_path
    zsh_path="$(command -v zsh || true)"
    local current_shell="${SHELL:-}"

    if [[ -z "$zsh_path" || "$current_shell" == "$zsh_path" ]]; then
        return
    fi

    if [[ ! -t 0 ]]; then
        echo "Skipping shell change prompt in non-interactive mode"
        return
    fi

    read -r -p "Set default shell to $zsh_path using chsh? [y/N] " response
    if [[ $response =~ ^[Yy]$ ]]; then
        run_cmd chsh -s "$zsh_path"
    fi
}

install_winget=false
install_windows_terminal=false
install_wsl=false
setup_wsl=false
setup_docker=false
dry_run=false
docker_image=""
host_override=""

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
        --host)
            host_override=$2
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
    ensure_deps zsh starship tmux neovim cargo stow
    clone_plugin_if_missing "$autosuggest_repo" "$plugin_root/zsh-autosuggestions"
    clone_plugin_if_missing "$syntax_highlight_repo" "$plugin_root/zsh-syntax-highlighting"

    dotfiles_args=()
    if [[ -n "$host_override" ]]; then
        if [[ ! -d "$repo_root/hosts/$host_override" ]]; then
            echo "Error: host overlay '$host_override' does not exist" >&2
            exit 1
        fi
        dotfiles_args+=(--host "$host_override")
    else
        detected_host="$(hostname 2>/dev/null || true)"
        if [[ -n "$detected_host" && -d "$repo_root/hosts/$detected_host" ]]; then
            dotfiles_args+=(--host "$detected_host")
        fi
    fi
    if [[ -f "$scripts/install_dotfiles.sh" ]]; then
        run_cmd bash "$scripts/install_dotfiles.sh" "${dotfiles_args[@]}"
    fi

    prompt_set_default_shell
    install_terminal_emulator

    run_cmd bash "$scripts/setup-hooks.sh"
    run_cmd bash "$scripts/helpers/install_fonts.sh"
    run_cmd bash "$scripts/helpers/sync_palettes.sh"
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
    if $setup_wsl; then run_cmd bash "$scripts/setup-wsl.sh"; fi
    if $setup_docker; then
        args=()
        [[ -n $docker_image ]] && args+=("--image" "$docker_image")
        run_cmd bash "$scripts/setup-docker.sh" "${args[@]}"
    fi
fi
