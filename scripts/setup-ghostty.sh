#!/usr/bin/env bash
set -euo pipefail

detect_ostype() {
    if [[ -n "${OSTYPE:-}" ]]; then
        printf '%s' "${OSTYPE,,}"
    else
        uname -s | tr '[:upper:]' '[:lower:]'
    fi
}

run_with_optional_sudo() {
    if [[ ${EUID:-$(id -u)} -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
    fi
}

install_ghostty_with_pkg_manager() {
    local normalized_ostype
    normalized_ostype="$(detect_ostype)"

    if [[ "$normalized_ostype" == darwin* ]] && command -v brew >/dev/null 2>&1; then
        brew install --cask ghostty
        return 0
    fi

    if [[ "$normalized_ostype" == linux* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            run_with_optional_sudo apt-get update
            run_with_optional_sudo apt-get install -y ghostty
            return 0
        elif command -v dnf >/dev/null 2>&1; then
            run_with_optional_sudo dnf install -y ghostty
            return 0
        elif command -v pacman >/dev/null 2>&1; then
            run_with_optional_sudo pacman -S --noconfirm ghostty
            return 0
        fi
    fi
    return 1
}

ensure_ghostty_installed() {
    if command -v ghostty >/dev/null 2>&1; then
        echo "Ghostty already installed; skipping install"
        return
    fi

    if install_ghostty_with_pkg_manager && command -v ghostty >/dev/null 2>&1; then
        echo "Installed Ghostty via native package manager"
        return
    fi

    echo "Falling back to cargo for Ghostty install"
    if ! command -v cargo >/dev/null 2>&1; then
        echo "Error: cargo is required for Ghostty fallback installation" >&2
        exit 1
    fi
    cargo install --locked ghostty
}

ensure_ghostty_installed

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
profile_script="$config_home/tino/terminal-profile.sh"
if [[ ! -x "$profile_script" ]]; then
    echo "Error: missing terminal profile contract at $profile_script" >&2
    exit 1
fi

"$profile_script" ghostty

echo "Ghostty installed and configured."
