#!/usr/bin/env bash
set -euo pipefail

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

providers=(ghostty wezterm kitty alacritty windows-terminal)
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

echo "Renderer contract validation passed for ${#providers[@]} providers."
