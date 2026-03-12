#!/usr/bin/env bash
set -euo pipefail

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
tino_dir="$config_home/tino"

source_if_exists() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        # shellcheck disable=SC1090
        source "$file_path"
    fi
}

# Contract fields shared across renderers.
readonly TINO_TERMINAL_CONTRACT_FIELDS=(
    TINO_TERMINAL_FPS
    TINO_TERMINAL_OPACITY
    TINO_TERMINAL_EFFECTS
)

readonly TINO_TERMINAL_PROVIDER_DEFAULT_ORDER=(
    ghostty
    wezterm
    kitty
    alacritty
)

terminal_is_windows_host() {
    case "${OSTYPE:-}" in
        msys*|cygwin*|win32*)
            return 0
            ;;
    esac

    if [[ "${OS:-}" == "Windows_NT" ]]; then
        return 0
    fi

    return 1
}

terminal_canonical_provider() {
    local override_provider="${TINO_TERMINAL_CANONICAL_PROVIDER:-}"

    case "$override_provider" in
        ghostty|wezterm|kitty|alacritty|windows-terminal)
            printf '%s\n' "$override_provider"
            return 0
            ;;
        "")
            ;;
        *)
            ;;
    esac

    if terminal_is_windows_host; then
        printf 'windows-terminal\n'
        return 0
    fi

    printf 'ghostty\n'
}

readonly TINO_TERMINAL_CONTRACT_PROVIDERS=(
    ghostty
    wezterm
    kitty
    alacritty
    windows-terminal
)

terminal_provider_preferences() {
    local raw_preferences="${TINO_TERMINAL_PROVIDER_PREFERENCES:-}"
    local -a normalized=()
    local -a combined=()
    local candidate=""

    if [[ -n "$raw_preferences" ]]; then
        raw_preferences="${raw_preferences//,/ }"
        for candidate in $raw_preferences; do
            case "$candidate" in
                ghostty|wezterm|kitty|alacritty)
                    normalized+=("$candidate")
                    ;;
            esac
        done
    fi

    combined=("$(terminal_canonical_provider)" "${normalized[@]}" "${TINO_TERMINAL_PROVIDER_DEFAULT_ORDER[@]}")

    awk '!seen[$0]++' < <(printf '%s\n' "${combined[@]}")
}

terminal_capability_status() {
    local provider="$1"
    local field="$2"

    case "$provider:$field" in
        ghostty:TINO_TERMINAL_FPS|ghostty:TINO_TERMINAL_OPACITY|ghostty:TINO_TERMINAL_EFFECTS)
            printf 'applied'
            ;;
        wezterm:TINO_TERMINAL_FPS|wezterm:TINO_TERMINAL_OPACITY)
            printf 'applied'
            ;;
        wezterm:TINO_TERMINAL_EFFECTS)
            printf 'unsupported'
            ;;
        kitty:TINO_TERMINAL_FPS|kitty:TINO_TERMINAL_OPACITY)
            printf 'applied'
            ;;
        kitty:TINO_TERMINAL_EFFECTS)
            printf 'unsupported'
            ;;
        alacritty:TINO_TERMINAL_OPACITY)
            printf 'applied'
            ;;
        alacritty:TINO_TERMINAL_FPS|alacritty:TINO_TERMINAL_EFFECTS)
            printf 'unsupported'
            ;;
        windows-terminal:TINO_TERMINAL_OPACITY|windows-terminal:TINO_TERMINAL_EFFECTS)
            printf 'applied'
            ;;
        windows-terminal:TINO_TERMINAL_FPS)
            printf 'unsupported'
            ;;
        *)
            printf 'unknown'
            ;;
    esac
}

load_terminal_profile() {
    source_if_exists "$tino_dir/terminal-defaults.sh"
    source_if_exists "$tino_dir/host-overrides.sh"

    export TINO_TERMINAL_FONT_FAMILY="${TINO_TERMINAL_FONT_FAMILY:-CaskaydiaCove Nerd Font}"
    export TINO_TERMINAL_FONT_SIZE="${TINO_TERMINAL_FONT_SIZE:-13}"
    export TINO_TERMINAL_OPACITY="${TINO_TERMINAL_OPACITY:-0.92}"
    export TINO_TERMINAL_FPS="${TINO_TERMINAL_FPS:-120}"
    export TINO_TERMINAL_EFFECTS="${TINO_TERMINAL_EFFECTS:-on}"

    export TINO_TERMINAL_BACKGROUND="${TINO_TERMINAL_BACKGROUND:-#000000}"
    export TINO_TERMINAL_FOREGROUND="${TINO_TERMINAL_FOREGROUND:-#f2f2f2}"
    export TINO_TERMINAL_CURSOR="${TINO_TERMINAL_CURSOR:-#FC17DA}"
    export TINO_TERMINAL_SELECTION="${TINO_TERMINAL_SELECTION:-#301050}"

    export TINO_TERMINAL_COLOR_0="${TINO_TERMINAL_COLOR_0:-#000000}"
    export TINO_TERMINAL_COLOR_1="${TINO_TERMINAL_COLOR_1:-#ff66c4}"
    export TINO_TERMINAL_COLOR_2="${TINO_TERMINAL_COLOR_2:-#b2ff59}"
    export TINO_TERMINAL_COLOR_3="${TINO_TERMINAL_COLOR_3:-#ffff66}"
    export TINO_TERMINAL_COLOR_4="${TINO_TERMINAL_COLOR_4:-#66b2ff}"
    export TINO_TERMINAL_COLOR_5="${TINO_TERMINAL_COLOR_5:-#845CFF}"
    export TINO_TERMINAL_COLOR_6="${TINO_TERMINAL_COLOR_6:-#66fff2}"
    export TINO_TERMINAL_COLOR_7="${TINO_TERMINAL_COLOR_7:-#f2f2f2}"
    export TINO_TERMINAL_COLOR_8="${TINO_TERMINAL_COLOR_8:-#666666}"
    export TINO_TERMINAL_COLOR_9="${TINO_TERMINAL_COLOR_9:-#ff66c4}"
    export TINO_TERMINAL_COLOR_10="${TINO_TERMINAL_COLOR_10:-#b2ff59}"
    export TINO_TERMINAL_COLOR_11="${TINO_TERMINAL_COLOR_11:-#ffff66}"
    export TINO_TERMINAL_COLOR_12="${TINO_TERMINAL_COLOR_12:-#66b2ff}"
    export TINO_TERMINAL_COLOR_13="${TINO_TERMINAL_COLOR_13:-#FC17DA}"
    export TINO_TERMINAL_COLOR_14="${TINO_TERMINAL_COLOR_14:-#66fff2}"
    export TINO_TERMINAL_COLOR_15="${TINO_TERMINAL_COLOR_15:-#ffffff}"
}

normalize_effects() {
    printf '%s' "${1,,}"
}

is_effects_enabled() {
    local normalized
    normalized="$(normalize_effects "$1")"
    case "$normalized" in
        off|false|no|0|none)
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

render_provider() {
    local provider="$1"
    local repo_root="${2:-}"

    load_terminal_profile

    case "$provider" in
        ghostty)
            "$tino_dir/renderers/ghostty.sh"
            ;;
        wezterm)
            "$tino_dir/renderers/wezterm.sh"
            ;;
        kitty)
            "$tino_dir/renderers/kitty.sh"
            ;;
        alacritty)
            "$tino_dir/renderers/alacritty.sh"
            ;;
        windows-terminal)
            "$tino_dir/renderers/windows-terminal.sh" "$repo_root"
            ;;
        *)
            echo "Unsupported terminal provider: $provider" >&2
            return 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    if [[ ${1:-} == "--provider-preferences" ]]; then
        terminal_provider_preferences
        exit 0
    fi

    if [[ ${1:-} == "--canonical-provider" ]]; then
        terminal_canonical_provider
        exit 0
    fi

    if [[ $# -lt 1 ]]; then
        echo "Usage: $(basename "$0") <provider> [repo-root]" >&2
        exit 1
    fi
    render_provider "$@"
fi
