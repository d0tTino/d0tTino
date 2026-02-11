#!/usr/bin/env bash
set -euo pipefail

provider="${1:-}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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
            command -v wezterm >/dev/null 2>&1 || install_with_pkg_manager wezterm || true
            ;;
        kitty)
            command -v kitty >/dev/null 2>&1 || install_with_pkg_manager kitty || true
            ;;
        alacritty)
            command -v alacritty >/dev/null 2>&1 || install_with_pkg_manager alacritty || true
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
    python "$repo_root/windows-terminal/generate_settings.py" \
      "$repo_root/windows-terminal/settings.base.json" \
      "$repo_root/windows-terminal/settings.json" \
      --terminal-overrides "$repo_root/windows-terminal/terminal-profile-overrides.json"
fi

echo "Terminal provider configured: $provider"
