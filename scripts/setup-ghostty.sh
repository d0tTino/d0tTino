#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
canonical_template="$repo_root/dotfiles/terminal/.config/tino/ghostty.toml.tmpl"
terminal_provider_setup="$repo_root/scripts/setup-terminal-provider.sh"

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
        echo "Error: unable to install Ghostty (cargo is required for fallback installation)" >&2
        exit 1
    fi
    if ! cargo install --locked ghostty; then
        echo "Error: unable to install Ghostty" >&2
        exit 1
    fi

    if ! command -v ghostty >/dev/null 2>&1; then
        echo "Error: unable to install Ghostty" >&2
        exit 1
    fi
}

sync_template() {
    local target_template="$1"
    local target_dir
    target_dir="$(dirname "$target_template")"
    mkdir -p "$target_dir"

    if [[ ! -f "$target_template" ]] || ! cmp -s "$canonical_template" "$target_template"; then
        cp "$canonical_template" "$target_template"
    fi
}

ensure_ghostty_installed

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
if [[ ! -f "$canonical_template" ]]; then
    echo "Error: missing canonical Ghostty template at $canonical_template" >&2
    exit 1
fi
if [[ ! -x "$terminal_provider_setup" ]]; then
    echo "Error: missing terminal provider setup at $terminal_provider_setup" >&2
    exit 1
fi

template_file="$config_home/tino/ghostty.toml.tmpl"
sync_template "$template_file"

bash "$terminal_provider_setup" ghostty

echo "Ghostty installed and configured."
