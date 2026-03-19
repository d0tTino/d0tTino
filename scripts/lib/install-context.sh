#!/usr/bin/env bash

if [[ -n "${TINO_INSTALL_CONTEXT_LIB_SOURCED:-}" ]]; then
    return 0
fi
TINO_INSTALL_CONTEXT_LIB_SOURCED=1

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

normalize_ostype() {
    local raw_ostype="${1:-${OSTYPE:-}}"

    if [[ -z "$raw_ostype" ]]; then
        raw_ostype="$(uname -s 2>/dev/null || true)"
    fi

    case "$raw_ostype" in
        CYGWIN*|cygwin*) printf '%s\n' 'cygwin' ;;
        MINGW*|mingw*|MSYS*|msys*) printf '%s\n' 'msys' ;;
        Windows_NT*) printf '%s\n' 'windows' ;;
        *) printf '%s\n' "${raw_ostype,,}" ;;
    esac
}

terminal_provider_supported() {
    case "$1" in
        ghostty|wezterm|kitty|alacritty|windows-terminal)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

resolve_host_overlay() {
    local raw_host="$1"
    local hosts_root="${2:-$repo_root/hosts}"

    [[ -z "$raw_host" ]] && return 0

    local normalized_lower="${raw_host,,}"
    local normalized_slug
    normalized_slug="$(printf '%s' "$normalized_lower" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"
    local short_host="${normalized_lower%%.*}"
    local short_slug
    short_slug="$(printf '%s' "$short_host" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"

    local -a candidates=("$raw_host" "$normalized_lower" "$normalized_slug" "$short_host" "$short_slug")
    local candidate
    for candidate in "${candidates[@]}"; do
        [[ -z "$candidate" ]] && continue
        if [[ -d "$hosts_root/$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
}

resolve_terminal_provider() {
    local resolved_host="${1:-}"
    local provider_override="${2:-}"
    local normalized_ostype
    normalized_ostype="$(normalize_ostype "${3:-${OSTYPE:-}}")"
    local provider=""
    local defaults_path="$repo_root/dotfiles/terminal/.config/tino/terminal-defaults.sh"
    local host_override_path=""

    if [[ -f "$defaults_path" ]]; then
        # shellcheck disable=SC1090
        source "$defaults_path"
    fi

    if [[ -n "$resolved_host" ]]; then
        host_override_path="$repo_root/hosts/$resolved_host/.config/tino/host-overrides.sh"
        if [[ -f "$host_override_path" ]]; then
            # shellcheck disable=SC1090
            source "$host_override_path"
        fi
    fi

    provider="${provider_override:-${TINO_TERMINAL_PROVIDER:-}}"
    if [[ -z "$provider" ]]; then
        case "$normalized_ostype" in
            msys*|cygwin*|win32*|windows*) provider='windows-terminal' ;;
            *) provider='ghostty' ;;
        esac
    fi

    if ! terminal_provider_supported "$provider"; then
        echo "Error: unsupported terminal provider '$provider' (supported: ghostty|wezterm|kitty|alacritty|windows-terminal)" >&2
        return 1
    fi

    printf '%s\n' "$provider"
}

resolve_nvim_benchmark_threshold_from_config() {
    local host_name="$1"
    local host_override_path=""

    if [[ -n "$host_name" ]]; then
        host_override_path="$repo_root/hosts/$host_name/.config/tino/host-overrides.sh"
        if [[ -f "$host_override_path" ]]; then
            local host_threshold=""
            local profile_default_threshold=""
            host_threshold="$({ source "$host_override_path"; printf '%s' "${TINO_NVIM_MAX_STARTUP_MS:-}"; })"
            profile_default_threshold="$({ source "$host_override_path"; printf '%s' "${TINO_NVIM_PROFILE_DEFAULT_MAX_STARTUP_MS:-}"; })"
            if [[ -n "$host_threshold" ]]; then
                printf '%s\n' "$host_threshold"
                return 0
            fi
            if [[ -n "$profile_default_threshold" ]]; then
                printf '%s\n' "$profile_default_threshold"
                return 0
            fi
        fi
    fi
}
