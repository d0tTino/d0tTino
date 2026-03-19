#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scripts="$repo_root/scripts"
# shellcheck source=scripts/lib/install-context.sh
source "$scripts/lib/install-context.sh"

OSTYPE="$(normalize_ostype "${OSTYPE:-}")"

run_cmd() {
    if $dry_run; then
        echo "$*"
    else
        "$@"
    fi
}

command_available_for_dep() {
    local dep=$1
    case "$dep" in
        neovim)
            command -v nvim >/dev/null 2>&1
            ;;
        fd)
            command -v fd >/dev/null 2>&1 || command -v fdfind >/dev/null 2>&1
            ;;
        *)
            command -v "$dep" >/dev/null 2>&1
            ;;
    esac
}

detect_linux_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    else
        echo ""
    fi
}

map_dep_to_package() {
    local dep=$1
    local manager=$2

    case "$dep" in
        rg)
            echo "ripgrep"
            ;;
        fd)
            if [[ $manager == "apt" || $manager == "dnf" ]]; then
                echo "fd-find"
            else
                echo "fd"
            fi
            ;;
        *)
            echo "$dep"
            ;;
    esac
}

build_install_package_list() {
    local manager=$1
    shift

    local packages=()
    local dep pkg seen
    for dep in "$@"; do
        pkg="$(map_dep_to_package "$dep" "$manager")"
        seen=false
        for existing in "${packages[@]}"; do
            if [[ $existing == "$pkg" ]]; then
                seen=true
                break
            fi
        done
        if ! $seen; then
            packages+=("$pkg")
        fi
    done

    printf '%s\n' "${packages[@]}"
}

ensure_deps() {
    local missing=()
    local cmd
    for cmd in "$@"; do
        if ! command_available_for_dep "$cmd"; then
            missing+=("$cmd")
        fi
    done

    if (( ${#missing[@]} > 0 )); then
        local manager=""
        local -a install_packages=()

        if [[ $OSTYPE == darwin* ]]; then
            if command -v brew >/dev/null 2>&1; then
                manager="brew"
                while IFS= read -r pkg; do
                    [[ -n $pkg ]] && install_packages+=("$pkg")
                done < <(build_install_package_list "$manager" "${missing[@]}")
                echo "Installing ${missing[*]} with Homebrew" >&2
                run_cmd brew install "${install_packages[@]}"
            else
                echo "Missing ${missing[*]}" >&2
                echo "Install Homebrew from https://brew.sh and run: brew install ${missing[*]}" >&2
                exit 1
            fi
        elif [[ $OSTYPE == linux* ]]; then
            manager="$(detect_linux_pkg_manager)"
            while IFS= read -r pkg; do
                [[ -n $pkg ]] && install_packages+=("$pkg")
            done < <(build_install_package_list "$manager" "${missing[@]}")

            if [[ $manager == "apt" ]]; then
                echo "Installing ${missing[*]} with apt-get" >&2
                run_cmd sudo apt-get update
                run_cmd sudo apt-get install -y "${install_packages[@]}"
            elif [[ $manager == "dnf" ]]; then
                echo "Installing ${missing[*]} with dnf" >&2
                run_cmd sudo dnf install -y "${install_packages[@]}"
            elif [[ $manager == "pacman" ]]; then
                echo "Installing ${missing[*]} with pacman" >&2
                run_cmd sudo pacman -S --noconfirm "${install_packages[@]}"
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

install_terminal_provider() {
    local provider="$1"

    if [[ ! -f "$scripts/setup-terminal-provider.sh" ]]; then
        return
    fi

    run_cmd bash "$scripts/setup-terminal-provider.sh" "$provider"
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
tmux_plugin_root="$HOME/.tmux/plugins"
tpm_repo="https://github.com/tmux-plugins/tpm"

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

get_login_shell() {
    local shell_path=""
    local user_name="${USER:-$(id -un 2>/dev/null || true)}"

    if [[ -z "$user_name" ]]; then
        shell_path="${SHELL:-unknown}"
        echo "$shell_path"
        return
    fi

    if [[ $OSTYPE == darwin* ]] && command -v dscl >/dev/null 2>&1; then
        shell_path="$(dscl . -read "/Users/$user_name" UserShell 2>/dev/null | awk '{print $2}' || true)"
    elif command -v getent >/dev/null 2>&1; then
        shell_path="$(getent passwd "$user_name" | cut -d: -f7 || true)"
    else
        shell_path="$(awk -F: -v user="$user_name" '$1 == user {print $7}' /etc/passwd 2>/dev/null || true)"
    fi

    if [[ -z "$shell_path" ]]; then
        shell_path="${SHELL:-unknown}"
    fi

    echo "$shell_path"
}

set_default_shell() {
    local mode="$1"
    local zsh_path current_shell final_shell action_message=""
    zsh_path="$(command -v zsh || true)"
    current_shell="$(get_login_shell)"

    if [[ -z "$zsh_path" ]]; then
        echo "Default shell unchanged: zsh is not installed or not in PATH"
        echo "Final login shell: $current_shell"
        echo "Action: install zsh and rerun with --set-default-shell=force (or prompt interactively)."
        return
    fi

    if [[ "$current_shell" == "$zsh_path" ]]; then
        echo "Default shell already set to zsh ($zsh_path)"
        echo "Final login shell: $current_shell"
        return
    fi

    case "$mode" in
        force)
            echo "Forcing default shell change to $zsh_path"
            if run_cmd chsh -s "$zsh_path"; then
                action_message=""
            else
                echo "Failed to change shell with 'chsh -s $zsh_path'. This may require a password, TTY, or elevated policy permissions." >&2
                action_message="Run manually: chsh -s $zsh_path"
            fi
            ;;
        prompt)
            if [[ ! -t 0 ]]; then
                echo "Skipping shell change prompt in non-interactive mode"
                action_message="deferred action required: run 'chsh -s $zsh_path'"
            else
                read -r -p "Set default shell to $zsh_path using chsh? [y/N] " response
                if [[ $response =~ ^[Yy]$ ]]; then
                    if run_cmd chsh -s "$zsh_path"; then
                        action_message=""
                    else
                        echo "Failed to change shell with 'chsh -s $zsh_path'." >&2
                        action_message="Run manually: chsh -s $zsh_path"
                    fi
                else
                    action_message="Run manually when ready: chsh -s $zsh_path"
                fi
            fi
            ;;
        skip)
            echo "Skipping default shell change (--set-default-shell=skip)"
            action_message="If desired later, run: chsh -s $zsh_path"
            ;;
        *)
            echo "Error: unsupported --set-default-shell mode '$mode' (expected: prompt, force, skip)" >&2
            exit 1
            ;;
    esac

    final_shell="$(get_login_shell)"
    echo "Final login shell: $final_shell"

    if [[ "$final_shell" != "$zsh_path" ]]; then
        if [[ -z "$action_message" ]]; then
            action_message="Run manually: chsh -s $zsh_path"
        fi
        echo "Action: default shell was not changed. $action_message"
    fi
}

install_winget=false
install_windows_terminal=false
terminal_provider=""
install_wsl=false
setup_wsl=false
setup_docker=false
dry_run=false
docker_image=""
host_override=""
set_default_shell_mode="prompt"

while [[ $# -gt 0 ]]; do
    case $1 in
        --winget)
            install_winget=true
            ;;
        --windows-terminal)
            install_windows_terminal=true
            ;;
        --terminal)
            terminal_provider=$2
            shift
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
        --set-default-shell)
            if [[ $# -gt 1 && $2 != --* ]]; then
                set_default_shell_mode=$2
                shift
            else
                set_default_shell_mode="prompt"
            fi
            ;;
        --set-default-shell=*)
            set_default_shell_mode="${1#*=}"
            ;;
        *)
            ;;
    esac
    shift
done

if [[ -n "$terminal_provider" ]] && ! terminal_provider_supported "$terminal_provider"; then
    echo "Error: unsupported --terminal provider '$terminal_provider'" >&2
    exit 1
fi

resolved_host=""
if [[ -n "$host_override" ]]; then
    resolved_host="$host_override"
else
    detected_host="$(hostname 2>/dev/null || true)"
    resolved_host="$(resolve_host_overlay "$detected_host")"
fi

if [[ -z "$terminal_provider" ]]; then
    terminal_provider="$(resolve_terminal_provider "$resolved_host")"
fi

if ! terminal_provider_supported "$terminal_provider"; then
    echo "Error: unsupported terminal provider '$terminal_provider' (supported: ghostty|wezterm|kitty|alacritty|windows-terminal)" >&2
    exit 1
fi

# Ensure core utilities are available
ensure_deps curl unzip git

if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    run_pwsh fix-path.ps1
    run_pwsh helpers/install_common.ps1
else
    ensure_deps zsh starship tmux neovim stow rg fd
    clone_plugin_if_missing "$autosuggest_repo" "$plugin_root/zsh-autosuggestions"
    clone_plugin_if_missing "$syntax_highlight_repo" "$plugin_root/zsh-syntax-highlighting"
    clone_plugin_if_missing "$tpm_repo" "$tmux_plugin_root/tpm"

    if [[ -n "$host_override" && ! -d "$repo_root/hosts/$host_override" ]]; then
        echo "Error: host overlay '$host_override' does not exist" >&2
        exit 1
    fi
    if [[ -f "$scripts/setup-nvim.sh" ]]; then
        benchmark_env=()
        setup_nvim_host="${host_override:-${resolved_host:-}}"
        if [[ -z "${TINO_NVIM_BENCHMARK_STARTUP:-}" && "$setup_nvim_host" == "desktop" ]]; then
            benchmark_env+=(TINO_NVIM_BENCHMARK_STARTUP=1)
        fi
        if [[ -z "${TINO_NVIM_MAX_STARTUP_MS:-}" ]]; then
            resolved_nvim_threshold="$(resolve_nvim_benchmark_threshold_from_config "$setup_nvim_host")"
            if [[ -n "$resolved_nvim_threshold" ]]; then
                benchmark_env+=(TINO_NVIM_MAX_STARTUP_MS="$resolved_nvim_threshold")
            fi
        fi
        run_cmd env "${benchmark_env[@]}" bash "$scripts/setup-nvim.sh"
    fi

    set_default_shell "$set_default_shell_mode"

    run_cmd bash "$scripts/setup-hooks.sh"
    run_cmd bash "$scripts/helpers/install_fonts.sh"
    run_cmd bash "$scripts/helpers/sync_palettes.sh"
fi

if [[ $OSTYPE == msys* || $OSTYPE == cygwin* || $OSTYPE == win32* || $OSTYPE == windows* ]]; then
    if $install_winget; then run_pwsh setup-winget.ps1; fi
    if [[ "$terminal_provider" == "windows-terminal" ]]; then
        install_windows_terminal=true
    fi

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
