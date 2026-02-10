#!/usr/bin/env bash
set -euo pipefail

# Install Ghostty via native package manager first, then cargo fallback.
# This script also provisions the repository-managed rich profile
# (font, Blacklight colors, opacity, and UI polish settings).
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

    if [[ "$normalized_ostype" == darwin* ]]; then
        if command -v brew >/dev/null 2>&1; then
            brew install --cask ghostty
            return
        fi
        return
    fi

    if [[ "$normalized_ostype" == linux* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            run_with_optional_sudo apt-get update
            run_with_optional_sudo apt-get install -y ghostty
            return
        fi

        if command -v dnf >/dev/null 2>&1; then
            run_with_optional_sudo dnf install -y ghostty
            return
        fi

        if command -v pacman >/dev/null 2>&1; then
            run_with_optional_sudo pacman -S --noconfirm ghostty
            return
        fi
    fi
}

ensure_ghostty_installed() {
    if command -v ghostty >/dev/null 2>&1; then
        echo "Ghostty already installed; skipping install"
        return
    fi

    if install_ghostty_with_pkg_manager; then
        if command -v ghostty >/dev/null 2>&1; then
            echo "Installed Ghostty via native package manager"
            return
        fi
    fi

    echo "Native package manager install unavailable or did not provide 'ghostty'; falling back to cargo"

    if command -v cargo >/dev/null 2>&1; then
        echo "Using existing cargo to install Ghostty"
        cargo install --locked ghostty
    else
        local normalized_ostype
        normalized_ostype="$(detect_ostype)"

        if [[ "$normalized_ostype" == darwin* ]] && command -v brew >/dev/null 2>&1; then
            echo "cargo not found; installing rustup/cargo with Homebrew for Ghostty fallback"
            brew install rustup-init
            rustup-init -y
            export PATH="$HOME/.cargo/bin:$PATH"
        elif [[ "$normalized_ostype" == linux* ]]; then
            if command -v apt-get >/dev/null 2>&1; then
                echo "cargo not found; installing cargo with apt-get for Ghostty fallback"
                run_with_optional_sudo apt-get update
                run_with_optional_sudo apt-get install -y cargo
            elif command -v dnf >/dev/null 2>&1; then
                echo "cargo not found; installing cargo with dnf for Ghostty fallback"
                run_with_optional_sudo dnf install -y cargo
            elif command -v pacman >/dev/null 2>&1; then
                echo "cargo not found; installing cargo with pacman for Ghostty fallback"
                run_with_optional_sudo pacman -S --noconfirm cargo
            fi
        fi

        if ! command -v cargo >/dev/null 2>&1; then
            echo "Error: unable to install Ghostty via native package manager and cargo is unavailable." >&2
            echo "Install Rust/Cargo (https://rustup.rs) and re-run this script to use the cargo fallback." >&2
            exit 1
        fi

        echo "Using newly installed cargo to install Ghostty"
        cargo install --locked ghostty
    fi

    if ! command -v ghostty >/dev/null 2>&1; then
        echo "Error: Ghostty install completed but 'ghostty' binary is still unavailable" >&2
        exit 1
    fi

    echo "Installed Ghostty via cargo"
}

ensure_ghostty_installed

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
config_dir="$config_home/ghostty"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
canonical_template="$repo_root/dotfiles/ghostty/ghostty.toml.tmpl"
config_file="$config_dir/ghostty.toml"
mkdir -p "$config_dir"

if [[ ! -f "$canonical_template" ]]; then
    echo "Error: managed Ghostty template is missing at $canonical_template" >&2
    exit 1
fi

source_if_exists() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        # shellcheck disable=SC1090
        source "$file_path"
    fi
}

# Load shared defaults first, then host-specific overrides from
# ~/.config/tino/host-overrides.sh using canonical
# TINO_TERMINAL_OPACITY/TINO_TERMINAL_FPS/TINO_TERMINAL_EFFECTS variables.
source_if_exists "$config_home/tino/terminal-defaults.sh"
source_if_exists "$config_home/tino/host-overrides.sh"

background_opacity="${TINO_TERMINAL_OPACITY:-0.92}"
max_fps="${TINO_TERMINAL_FPS:-120}"
effects="${TINO_TERMINAL_EFFECTS:-on}"

validate_number() {
    local value="$1"
    local name="$2"
    local pattern="$3"

    if [[ ! "$value" =~ $pattern ]]; then
        echo "Error: $name must be numeric, got '$value'" >&2
        exit 1
    fi
}

normalize_effects_to_toml() {
    local raw_value="$1"
    local value

    value="$(printf '%s' "$raw_value" | tr '[:upper:]' '[:lower:]')"
    case "$value" in
        high|balanced|on|true|yes|1)
            printf '%s' "true"
            ;;
        off|false|no|0|none)
            printf '%s' "false"
            ;;
        *.glsl|*/*)
            # Treat shader file paths as TOML strings.
            local escaped_value
            escaped_value="${raw_value//\\/\\\\}"
            escaped_value="${escaped_value//\"/\\\"}"
            printf '"%s"' "$escaped_value"
            ;;
        *)
            echo "Error: unknown TINO_TERMINAL_EFFECTS '$raw_value'. Use one of: on, off, balanced, high, true, false, or a shader path (*.glsl)." >&2
            exit 1
            ;;
    esac
}

validate_number "$background_opacity" "TINO_TERMINAL_OPACITY" '^[0-9]+([.][0-9]+)?$'
validate_number "$max_fps" "TINO_TERMINAL_FPS" '^[0-9]+$'
effects_toml="$(normalize_effects_to_toml "$effects")"

template_contents="$(<"$canonical_template")"
rendered_config="${template_contents//__BACKGROUND_OPACITY__/$background_opacity}"
rendered_config="${rendered_config//__MAX_FPS__/$max_fps}"
rendered_config="${rendered_config//__CUSTOM_SHADER__/$effects_toml}"

if [[ -f "$config_file" ]] && [[ "$(<"$config_file")" == "$rendered_config" ]]; then
    echo "Configuration already up to date at $config_file"
else
    printf '%s\n' "$rendered_config" >"$config_file"
    echo "Configuration rendered to $config_file"
fi

echo "Ghostty installed."
