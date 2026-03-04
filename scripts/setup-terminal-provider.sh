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
    if [[ "$provider" == "ghostty" ]] && command -v brew >/dev/null 2>&1; then
        brew install --cask ghostty && return 0
    fi
    if command -v brew >/dev/null 2>&1; then
        brew install "$pkg" && return 0
    fi

    run_with_optional_sudo() {
        if [[ ${EUID:-$(id -u)} -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
            sudo "$@"
        else
            "$@"
        fi
    }

    if command -v apt-get >/dev/null 2>&1; then
        run_with_optional_sudo apt-get update && run_with_optional_sudo apt-get install -y "$pkg" && return 0
    fi
    if command -v dnf >/dev/null 2>&1; then
        run_with_optional_sudo dnf install -y "$pkg" && return 0
    fi
    if command -v pacman >/dev/null 2>&1; then
        run_with_optional_sudo pacman -S --noconfirm "$pkg" && return 0
    fi
    return 1
}

report_unavailable_provider() {
    local install_url="$1"

    if [[ "$strict_mode" == "1" ]]; then
        echo "Error: $provider is still unavailable after installation attempt." >&2
        echo "Install $provider manually ($install_url) or set TINO_TERMINAL_STRICT=0 to continue without failing." >&2
        exit 1
    fi

    echo "Warning: $provider is still unavailable after installation attempt; continuing because TINO_TERMINAL_STRICT=$strict_mode." >&2
}

ensure_provider_installed() {
    case "$provider" in
        wezterm)
            if ! command -v wezterm >/dev/null 2>&1; then
                if ! install_with_pkg_manager wezterm; then
                    echo "Warning: automatic install for wezterm failed." >&2
                fi
            fi
            command -v wezterm >/dev/null 2>&1 || report_unavailable_provider "https://wezfurlong.org/wezterm/installation.html"
            ;;
        kitty)
            if ! command -v kitty >/dev/null 2>&1; then
                if ! install_with_pkg_manager kitty; then
                    echo "Warning: automatic install for kitty failed." >&2
                fi
            fi
            command -v kitty >/dev/null 2>&1 || report_unavailable_provider "https://sw.kovidgoyal.net/kitty/binary/"
            ;;
        alacritty)
            if ! command -v alacritty >/dev/null 2>&1; then
                if ! install_with_pkg_manager alacritty; then
                    echo "Warning: automatic install for alacritty failed." >&2
                fi
            fi
            command -v alacritty >/dev/null 2>&1 || report_unavailable_provider "https://github.com/alacritty/alacritty/blob/master/INSTALL.md"
            ;;
        ghostty)
            if ! command -v ghostty >/dev/null 2>&1; then
                if ! install_with_pkg_manager ghostty; then
                    echo "Warning: automatic install for ghostty failed." >&2
                fi
            fi

            if ! command -v ghostty >/dev/null 2>&1; then
                echo "Falling back to cargo for Ghostty install"
                if command -v cargo >/dev/null 2>&1; then
                    if ! cargo install --locked ghostty; then
                        echo "Warning: cargo fallback installation for ghostty failed." >&2
                    fi
                else
                    echo "Warning: cargo is unavailable for ghostty fallback installation." >&2
                fi
            fi

            command -v ghostty >/dev/null 2>&1 || report_unavailable_provider "https://ghostty.org/docs/install/binary"
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

ensure_provider_installed
"$profile_script" "$provider" "$repo_root"

if [[ "$provider" == "windows-terminal" ]]; then
    validate_windows_terminal_inputs
    python "$repo_root/windows-terminal/generate_settings.py" \
      "$repo_root/windows-terminal/settings.base.json" \
      "$repo_root/windows-terminal/settings.json" \
      --terminal-overrides "$repo_root/windows-terminal/terminal-profile-overrides.json"
fi

echo "Terminal provider configured: $provider"
