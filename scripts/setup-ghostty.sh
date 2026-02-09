#!/usr/bin/env bash
set -euo pipefail

# Install Ghostty via cargo if not already installed.
# This script also provisions the repository-managed rich profile
# (font, Blacklight colors, opacity, and UI polish settings).
if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo is required to install Ghostty" >&2
    exit 1
fi

if ! command -v ghostty >/dev/null 2>&1; then
    cargo install --locked ghostty
fi

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
# ~/.config/tino/host-overrides.sh using TINO_TERMINAL_* variables.
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
