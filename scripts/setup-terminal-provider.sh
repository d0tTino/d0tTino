#!/usr/bin/env bash
set -euo pipefail

provider="${1:-}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
strict_mode="${TINO_TERMINAL_STRICT:-1}"
persist_fallback_mode="${TINO_TERMINAL_PERSIST_FALLBACK:-0}"
selected_provider="$provider"
readonly TERMINAL_CAPABILITY_PROBE_ORDER=(ghostty wezterm kitty alacritty)

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

provider_binary() {
    local provider_name="$1"

    case "$provider_name" in
        ghostty|wezterm|kitty|alacritty)
            printf '%s' "$provider_name"
            ;;
        *)
            return 1
            ;;
    esac
}

provider_install_url() {
    local provider_name="$1"

    case "$provider_name" in
        ghostty)
            printf '%s' "https://ghostty.org/docs/install/binary"
            ;;
        wezterm)
            printf '%s' "https://wezfurlong.org/wezterm/installation.html"
            ;;
        kitty)
            printf '%s' "https://sw.kovidgoyal.net/kitty/binary/"
            ;;
        alacritty)
            printf '%s' "https://github.com/alacritty/alacritty/blob/master/INSTALL.md"
            ;;
        *)
            return 1
            ;;
    esac
}

provider_is_available() {
    local provider_name="$1"
    local binary

    binary="$(provider_binary "$provider_name")" || return 1
    command -v "$binary" >/dev/null 2>&1
}

report_unavailable_provider() {
    local provider_name="$1"
    local install_url
    install_url="$(provider_install_url "$provider_name")"

    if [[ "$strict_mode" == "1" ]]; then
        echo "Error: $provider_name is still unavailable after installation attempt." >&2
        echo "Install $provider_name manually ($install_url) or set TINO_TERMINAL_STRICT=0 to continue without failing." >&2
        exit 1
    fi

    echo "Warning: $provider_name is still unavailable after installation attempt; continuing because TINO_TERMINAL_STRICT=$strict_mode." >&2
}

attempt_provider_install() {
    local provider_name="$1"

    case "$provider_name" in
        wezterm)
            if ! command -v wezterm >/dev/null 2>&1; then
                if ! install_with_pkg_manager wezterm; then
                    echo "Warning: automatic install for wezterm failed." >&2
                fi
            fi
            ;;
        kitty)
            if ! command -v kitty >/dev/null 2>&1; then
                if ! install_with_pkg_manager kitty; then
                    echo "Warning: automatic install for kitty failed." >&2
                fi
            fi
            ;;
        alacritty)
            if ! command -v alacritty >/dev/null 2>&1; then
                if ! install_with_pkg_manager alacritty; then
                    echo "Warning: automatic install for alacritty failed." >&2
                fi
            fi
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

resolve_provider_via_capability_probe() {
    local -a candidates=()
    local candidate

    if [[ -x "$profile_script" ]]; then
        mapfile -t candidates < <("$profile_script" --provider-preferences 2>/dev/null || true)
    fi

    if [[ ${#candidates[@]} -eq 0 ]]; then
        candidates=("${TERMINAL_CAPABILITY_PROBE_ORDER[@]}")
    fi

    for candidate in "${candidates[@]}"; do
        if provider_is_available "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

upsert_host_override_provider() {
    local override_path="$1"
    local persisted_provider="$2"

    mkdir -p "$(dirname "$override_path")"

    if [[ ! -f "$override_path" ]]; then
        printf '# Host-specific overrides for tino.\n' >"$override_path"
    fi

    if rg -q '^export TINO_TERMINAL_PROVIDER=' "$override_path"; then
        python - "$override_path" "$persisted_provider" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
provider = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
updated = []
for line in lines:
    if line.startswith("export TINO_TERMINAL_PROVIDER="):
        updated.append(f'export TINO_TERMINAL_PROVIDER="{provider}"')
    else:
        updated.append(line)
path.write_text("\n".join(updated) + "\n", encoding="utf-8")
PY
        return
    fi

    if [[ -s "$override_path" ]]; then
        printf '\n' >>"$override_path"
    fi
    printf 'export TINO_TERMINAL_PROVIDER="%s"\n' "$persisted_provider" >>"$override_path"
}

handle_persisted_fallback_provider() {
    local requested_provider="$1"
    local fallback_provider="$2"
    local host_override_path="$XDG_CONFIG_TINO_DIR/host-overrides.sh"

    if [[ "$persist_fallback_mode" == "1" ]]; then
        upsert_host_override_provider "$host_override_path" "$fallback_provider"
        echo "Persisted fallback provider in $host_override_path: $requested_provider -> $fallback_provider" >&2
        return
    fi

    if [[ "$persist_fallback_mode" == "print" ]]; then
        echo "Fallback provider detected ($requested_provider -> $fallback_provider). Persist with:" >&2
        echo "  export TINO_TERMINAL_PROVIDER=\"$fallback_provider\"" >&2
        echo "Then add/update that line in $host_override_path for deterministic future sessions." >&2
    fi
}

ensure_provider_installed() {
    if [[ "$provider" == "windows-terminal" ]]; then
        return
    fi

    attempt_provider_install "$provider"
    if provider_is_available "$provider"; then
        selected_provider="$provider"
        return
    fi

    local fallback_provider=""
    if fallback_provider="$(resolve_provider_via_capability_probe)"; then
        selected_provider="$fallback_provider"
        if [[ "$selected_provider" != "$provider" ]]; then
            echo "Warning: preferred provider '$provider' is unavailable; using '$selected_provider' based on capability probe." >&2
            handle_persisted_fallback_provider "$provider" "$selected_provider"
        fi
        return
    fi

    report_unavailable_provider "$provider"
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
XDG_CONFIG_TINO_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/tino"
if [[ ! -x "$profile_script" ]]; then
    echo "Error: missing terminal profile contract at $profile_script" >&2
    exit 1
fi

ensure_provider_installed
"$profile_script" "$selected_provider" "$repo_root"

if [[ "$selected_provider" == "windows-terminal" ]]; then
    validate_windows_terminal_inputs
    python "$repo_root/windows-terminal/generate_settings.py" \
      "$repo_root/windows-terminal/settings.base.json" \
      "$repo_root/windows-terminal/settings.json" \
      --terminal-overrides "$repo_root/windows-terminal/terminal-profile-overrides.json"
fi

echo "Terminal provider configured: $selected_provider"
