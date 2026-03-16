#!/usr/bin/env bash
set -euo pipefail

report_format=""
report_file=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --report-format)
            report_format="${2:-}"
            shift 2
            ;;
        --report-file)
            report_file="${2:-}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if [[ -n "$report_format" ]]; then
    case "$report_format" in
        json|markdown)
            ;;
        *)
            echo "Unsupported report format: $report_format (expected: json, markdown)" >&2
            exit 1
            ;;
    esac
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

tmp_dir="$(mktemp -d)"
cleanup() {
    rm -rf "$tmp_dir"
}
trap cleanup EXIT

mkdir -p "$tmp_dir/.config"
ln -s "$repo_root/dotfiles/terminal/.config/tino" "$tmp_dir/.config/tino"

export HOME="$tmp_dir"
export XDG_CONFIG_HOME="$tmp_dir/.config"
# Force an effects value that must be propagated by renderers that support effects.
export TINO_TERMINAL_EFFECTS="/tmp/tino-shader.glsl"

# shellcheck disable=SC1090
source "$XDG_CONFIG_HOME/tino/terminal-profile.sh"

providers=("${TINO_TERMINAL_CONTRACT_PROVIDERS[@]}")
validation_repo_root="$tmp_dir/validation-repo"
mkdir -p "$validation_repo_root"
for provider in "${providers[@]}"; do
    "$XDG_CONFIG_HOME/tino/terminal-profile.sh" "$provider" "$validation_repo_root" >/dev/null
done

check_applied() {
    local provider="$1"
    local field="$2"

    case "$provider:$field" in
        ghostty:TINO_TERMINAL_FPS)
            rg -q '^custom-shader-animation-max-fps = ' "$XDG_CONFIG_HOME/ghostty/ghostty.toml"
            ;;
        ghostty:TINO_TERMINAL_OPACITY)
            rg -q '^background-opacity = ' "$XDG_CONFIG_HOME/ghostty/ghostty.toml"
            ;;
        ghostty:TINO_TERMINAL_EFFECTS)
            ! rg -q 'tino-contract:unsupported TINO_TERMINAL_EFFECTS' "$XDG_CONFIG_HOME/ghostty/ghostty.toml"
            ;;
        wezterm:TINO_TERMINAL_FPS)
            rg -q 'max_fps = ' "$XDG_CONFIG_HOME/wezterm/wezterm.generated.lua"
            ;;
        wezterm:TINO_TERMINAL_OPACITY)
            rg -q 'window_background_opacity = ' "$XDG_CONFIG_HOME/wezterm/wezterm.generated.lua"
            ;;
        kitty:TINO_TERMINAL_FPS)
            rg -q '^sync_to_monitor yes$' "$XDG_CONFIG_HOME/kitty/kitty.conf"
            rg -q '^repaint_delay [0-9]+$' "$XDG_CONFIG_HOME/kitty/kitty.conf"
            ;;
        kitty:TINO_TERMINAL_OPACITY)
            rg -q '^background_opacity ' "$XDG_CONFIG_HOME/kitty/kitty.conf"
            ;;
        alacritty:TINO_TERMINAL_OPACITY)
            rg -q '^opacity = ' "$XDG_CONFIG_HOME/alacritty/alacritty.toml"
            ;;
        windows-terminal:TINO_TERMINAL_OPACITY)
            rg -q '"acrylicOpacity"' "$validation_repo_root/windows-terminal/terminal-profile-overrides.json"
            ;;
        windows-terminal:TINO_TERMINAL_EFFECTS)
            rg -q '"useAcrylic"' "$validation_repo_root/windows-terminal/terminal-profile-overrides.json"
            ;;
        *)
            return 1
            ;;
    esac
}

check_unsupported() {
    local provider="$1"
    local field="$2"

    case "$provider:$field" in
        wezterm:TINO_TERMINAL_EFFECTS)
            rg -q '^-- tino-contract:unsupported TINO_TERMINAL_EFFECTS$' "$XDG_CONFIG_HOME/wezterm/wezterm.generated.lua"
            ;;
        kitty:TINO_TERMINAL_EFFECTS)
            rg -q '^# tino-contract:unsupported TINO_TERMINAL_EFFECTS$' "$XDG_CONFIG_HOME/kitty/kitty.conf"
            ;;
        alacritty:TINO_TERMINAL_FPS)
            rg -q '^# tino-contract:unsupported TINO_TERMINAL_FPS$' "$XDG_CONFIG_HOME/alacritty/alacritty.toml"
            ;;
        alacritty:TINO_TERMINAL_EFFECTS)
            rg -q '^# tino-contract:unsupported TINO_TERMINAL_EFFECTS$' "$XDG_CONFIG_HOME/alacritty/alacritty.toml"
            ;;
        windows-terminal:TINO_TERMINAL_FPS)
            rg -q '"TINO_TERMINAL_FPS"' "$validation_repo_root/windows-terminal/terminal-profile-overrides.json"
            ;;
        *)
            return 1
            ;;
    esac
}

symbol_for_status() {
    case "$1" in
        applied)
            printf '✅'
            ;;
        unsupported)
            printf '❌'
            ;;
        *)
            printf '❓'
            ;;
    esac
}


check_wezterm_fallback_schema() {
    local fallback_file="$repo_root/dotfiles/terminal/.config/wezterm/wezterm.lua"

    rg -q '^-- Safe baseline fallback when wezterm.generated.lua is unavailable\.$' "$fallback_file"
    rg -q '^    font = wezterm\.font_with_fallback\(\{$' "$fallback_file"
    rg -q '^    window_background_opacity = ' "$fallback_file"
    rg -q '^    use_fancy_tab_bar = false,$' "$fallback_file"
    rg -q '^    hide_tab_bar_if_only_one_tab = true,$' "$fallback_file"
    rg -q '^    window_padding = \{ left = [0-9]+, right = [0-9]+, top = [0-9]+, bottom = [0-9]+ \},$' "$fallback_file"
    rg -q '^    colors = \{$' "$fallback_file"
    rg -q '^        foreground = "#' "$fallback_file"
    rg -q '^        background = "#' "$fallback_file"
    rg -q '^        cursor_bg = "#' "$fallback_file"
    rg -q '^        cursor_fg = "#' "$fallback_file"
    rg -q '^        selection_bg = "#' "$fallback_file"
    rg -q '^        ansi = \{ .+ \},$' "$fallback_file"
    rg -q '^        brights = \{ .+ \},$' "$fallback_file"
}


build_report() {
    local format="$1"
    local output

    if [[ "$format" == "json" ]]; then
        output="{\"providers\":["
    else
        output="| Provider | FPS | Opacity | Effects |\n| --- | --- | --- | --- |"
    fi

    local first_provider=1
    local provider
    for provider in "${providers[@]}"; do
        if [[ "$format" == "json" ]]; then
            if [[ $first_provider -eq 0 ]]; then
                output+=","
            fi
            first_provider=0
            output+="{\"name\":\"$provider\",\"capabilities\":{"
        fi

        local first_field=1
        local field
        local fps=""
        local opacity=""
        local effects=""

        for field in "${TINO_TERMINAL_CONTRACT_FIELDS[@]}"; do
            local status
            status="$(terminal_capability_status "$provider" "$field")"
            if [[ "$format" == "json" ]]; then
                if [[ $first_field -eq 0 ]]; then
                    output+=","
                fi
                first_field=0
                output+="\"$field\":\"$status\""
            else
                case "$field" in
                    TINO_TERMINAL_FPS) fps="$(symbol_for_status "$status") $status" ;;
                    TINO_TERMINAL_OPACITY) opacity="$(symbol_for_status "$status") $status" ;;
                    TINO_TERMINAL_EFFECTS) effects="$(symbol_for_status "$status") $status" ;;
                esac
            fi
        done

        if [[ "$format" == "json" ]]; then
            output+="}}"
        else
            output+="\n| $provider | $fps | $opacity | $effects |"
        fi
    done

    if [[ "$format" == "json" ]]; then
        output+="]}"
    fi

    printf '%b\n' "$output"
}

check_wezterm_fallback_schema

for provider in "${providers[@]}"; do
    for field in "${TINO_TERMINAL_CONTRACT_FIELDS[@]}"; do
        status="$(terminal_capability_status "$provider" "$field")"
        if [[ "$status" == "applied" ]]; then
            check_applied "$provider" "$field"
        elif [[ "$status" == "unsupported" ]]; then
            check_unsupported "$provider" "$field"
        else
            echo "unknown capability status for ${provider}:${field}" >&2
            exit 1
        fi
    done

done

if [[ -n "$report_format" ]]; then
    report_payload="$(build_report "$report_format")"
    if [[ -n "$report_file" ]]; then
        mkdir -p "$(dirname "$report_file")"
        printf '%s\n' "$report_payload" > "$report_file"
    else
        printf '%s\n' "$report_payload"
    fi
fi

echo "Renderer contract validation passed for ${#providers[@]} providers."
