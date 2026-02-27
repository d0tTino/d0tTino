#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
canonical_template="$repo_root/dotfiles/terminal/.config/tino/ghostty.toml.tmpl"

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

render_ghostty_config() {
    local template_file="$1"
    local target_file="$2"
    local rendered custom_shader_line escaped_effects

    custom_shader_line=""
    case "${TINO_TERMINAL_EFFECTS,,}" in
        off|false|no|0|none|on|true|yes|1|balanced|high)
            ;;
        *)
            escaped_effects="${TINO_TERMINAL_EFFECTS//\"/\\\"}"
            custom_shader_line="custom-shader = \"${escaped_effects}\""
            ;;
    esac

    rendered="$(<"$template_file")"
    rendered="${rendered//__FONT_FAMILY__/$TINO_TERMINAL_FONT_FAMILY}"
    rendered="${rendered//__FONT_SIZE__/$TINO_TERMINAL_FONT_SIZE}"
    rendered="${rendered//__BACKGROUND__/$TINO_TERMINAL_BACKGROUND}"
    rendered="${rendered//__BACKGROUND_OPACITY__/$TINO_TERMINAL_OPACITY}"
    rendered="${rendered//__MAX_FPS__/$TINO_TERMINAL_FPS}"
    rendered="${rendered//__CUSTOM_SHADER_LINE__/$custom_shader_line}"
    rendered="${rendered//__CURSOR__/$TINO_TERMINAL_CURSOR}"

    for i in $(seq 0 15); do
        key="TINO_TERMINAL_COLOR_${i}"
        placeholder="__COLOR_${i}__"
        rendered="${rendered//${placeholder}/${!key}}"
    done

    mkdir -p "$(dirname "$target_file")"
    if [[ -f "$target_file" ]] && [[ "$(<"$target_file")" == "$rendered" ]]; then
        echo "Configuration already up to date at $target_file"
        return
    fi

    printf '%s\n' "$rendered" > "$target_file"
    echo "Configuration rendered at $target_file"
}

ensure_ghostty_installed

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
profile_script="$repo_root/dotfiles/terminal/.config/tino/terminal-profile.sh"
if [[ ! -f "$canonical_template" ]]; then
    echo "Error: missing canonical Ghostty template at $canonical_template" >&2
    exit 1
fi
if [[ ! -f "$profile_script" ]]; then
    echo "Error: missing terminal profile contract at $profile_script" >&2
    exit 1
fi

template_file="$config_home/tino/ghostty.toml.tmpl"
sync_template "$template_file"

# shellcheck disable=SC1090
source "$profile_script"
load_terminal_profile

render_ghostty_config "$template_file" "$config_home/ghostty/ghostty.toml"

echo "Ghostty installed and configured."
