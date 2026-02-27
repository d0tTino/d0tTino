#!/usr/bin/env bash
set -euo pipefail

provider="${1:-}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
strict_mode="${TINO_TERMINAL_STRICT:-1}"

if [[ -z "$provider" ]]; then
    echo "Usage: $(basename "$0") <ghostty|wezterm|kitty|alacritty|windows-terminal>" >&2
    exit 1
fi

install_with_pkg_manager() {
    local pkg="$1"
    if command -v brew >/dev/null 2>&1; then
        brew install "$pkg" && return 0
    fi
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y "$pkg" && return 0
    fi
    if command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y "$pkg" && return 0
    fi
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm "$pkg" && return 0
    fi
    return 1
}

ensure_provider_installed() {
    case "$provider" in
        ghostty)
            bash "$repo_root/scripts/setup-ghostty.sh"
            return
            ;;
        wezterm)
            if ! command -v wezterm >/dev/null 2>&1; then
                if ! install_with_pkg_manager wezterm; then
                    echo "Warning: automatic install for wezterm failed." >&2
                fi
            fi
            if ! command -v wezterm >/dev/null 2>&1; then
                if [[ "$strict_mode" == "1" ]]; then
                    echo "Error: wezterm is still unavailable after installation attempt." >&2
                    echo "Install wezterm manually (https://wezfurlong.org/wezterm/installation.html) or set TINO_TERMINAL_STRICT=0 to continue without failing." >&2
                    exit 1
                fi
                echo "Warning: wezterm is still unavailable after installation attempt; continuing because TINO_TERMINAL_STRICT=$strict_mode." >&2
            fi
            ;;
        kitty)
            if ! command -v kitty >/dev/null 2>&1; then
                if ! install_with_pkg_manager kitty; then
                    echo "Warning: automatic install for kitty failed." >&2
                fi
            fi
            if ! command -v kitty >/dev/null 2>&1; then
                if [[ "$strict_mode" == "1" ]]; then
                    echo "Error: kitty is still unavailable after installation attempt." >&2
                    echo "Install kitty manually (https://sw.kovidgoyal.net/kitty/binary/) or set TINO_TERMINAL_STRICT=0 to continue without failing." >&2
                    exit 1
                fi
                echo "Warning: kitty is still unavailable after installation attempt; continuing because TINO_TERMINAL_STRICT=$strict_mode." >&2
            fi
            ;;
        alacritty)
            if ! command -v alacritty >/dev/null 2>&1; then
                if ! install_with_pkg_manager alacritty; then
                    echo "Warning: automatic install for alacritty failed." >&2
                fi
            fi
            if ! command -v alacritty >/dev/null 2>&1; then
                if [[ "$strict_mode" == "1" ]]; then
                    echo "Error: alacritty is still unavailable after installation attempt." >&2
                    echo "Install alacritty manually (https://github.com/alacritty/alacritty/blob/master/INSTALL.md) or set TINO_TERMINAL_STRICT=0 to continue without failing." >&2
                    exit 1
                fi
                echo "Warning: alacritty is still unavailable after installation attempt; continuing because TINO_TERMINAL_STRICT=$strict_mode." >&2
            fi
            ;;
        windows-terminal)
            return
            ;;
        *)
            echo "Unsupported provider: $provider" >&2
            exit 1
            ;;
    esac
}

validate_windows_terminal_inputs() {
    local generator_script="$repo_root/windows-terminal/generate_settings.py"
    local base_settings="$repo_root/windows-terminal/settings.base.json"
    local overrides="$repo_root/windows-terminal/terminal-profile-overrides.json"
    local output="$repo_root/windows-terminal/settings.json"

    for path in "$generator_script" "$base_settings" "$overrides"; do
        if [[ ! -f "$path" ]]; then
            echo "Error: required Windows Terminal input is missing: $path" >&2
            exit 1
        fi
    done

    mkdir -p "$(dirname "$output")"
}

profile_script="${XDG_CONFIG_HOME:-$HOME/.config}/tino/terminal-profile.sh"
if [[ ! -x "$profile_script" ]]; then
    echo "Error: missing terminal profile contract at $profile_script" >&2
    exit 1
fi

if [[ "$provider" != "ghostty" ]]; then
    ensure_provider_installed
fi
"$profile_script" "$provider" "$repo_root"

if [[ "$provider" == "windows-terminal" ]]; then
    validate_windows_terminal_inputs
    python "$repo_root/windows-terminal/generate_settings.py" \
      "$repo_root/windows-terminal/settings.base.json" \
      "$repo_root/windows-terminal/settings.json" \
      --terminal-overrides "$repo_root/windows-terminal/terminal-profile-overrides.json"
fi

echo "Terminal provider configured: $provider"
