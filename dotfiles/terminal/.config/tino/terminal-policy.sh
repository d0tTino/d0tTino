#!/usr/bin/env bash
set -euo pipefail

terminal_policy_json_path() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    printf '%s/terminal-policy.json' "$script_dir"
}

terminal_policy_query() {
    local query="$1"
    local policy_json
    local python_bin
    python_bin="$(terminal_policy_python_bin)"
    policy_json="$(terminal_policy_json_path)"

    "$python_bin" - "$policy_json" "$query" <<'PY'
import json
import sys
from pathlib import Path

policy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
query = sys.argv[2]

if query == "host_profiles":
    print("\n".join(policy["host_profiles"].keys()))
    raise SystemExit(0)

if query.startswith("host_canonical:"):
    profile = query.split(":", 1)[1]
    print(policy["host_profiles"][profile]["canonical_provider"])
    raise SystemExit(0)

if query.startswith("host_approved:"):
    profile = query.split(":", 1)[1]
    print("\n".join(policy["host_profiles"][profile]["approved_providers"]))
    raise SystemExit(0)

if query.startswith("probe_order:"):
    profile = query.split(":", 1)[1]
    print("\n".join(policy["host_profiles"][profile]["provider_probe_order"]))
    raise SystemExit(0)

if query.startswith("capability:"):
    _, provider, field = query.split(":", 2)
    print(policy["providers"][provider]["capabilities"][field])
    raise SystemExit(0)

if query.startswith("setting:"):
    _, field, key = query.split(":", 2)
    value = policy["settings"][field][key]
    if isinstance(value, list):
        print("\n".join(str(item) for item in value))
    else:
        print(value)
    raise SystemExit(0)

raise SystemExit(f"unsupported policy query: {query}")
PY
}

terminal_policy_python_bin() {
    local python_bin="${PYTHON:-python3}"
    if ! command -v "$python_bin" >/dev/null 2>&1; then
        python_bin="python"
    fi
    printf '%s\n' "$python_bin"
}

terminal_policy_detect_host_profile() {
    case "${TINO_HOST_PROFILE:-}" in
        desktop|work_laptop|windows)
            printf '%s\n' "$TINO_HOST_PROFILE"
            return 0
            ;;
    esac

    case "${OSTYPE:-}" in
        msys*|cygwin*|win32*)
            printf 'windows\n'
            return 0
            ;;
    esac

    if [[ "${OS:-}" == "Windows_NT" ]]; then
        printf 'windows\n'
        return 0
    fi

    printf 'desktop\n'
}

terminal_policy_canonical_provider() {
    local host_profile="$1"
    terminal_policy_query "host_canonical:${host_profile}"
}

terminal_policy_approved_providers() {
    local host_profile="$1"
    terminal_policy_query "host_approved:${host_profile}"
}

terminal_policy_probe_order() {
    local host_profile="$1"
    terminal_policy_query "probe_order:${host_profile}"
}

terminal_policy_capability_status() {
    local provider="$1"
    local field="$2"
    terminal_policy_query "capability:${provider}:${field}"
}

clamp_terminal_policy_values() {
    local fps_default fps_min fps_max opacity_default opacity_min opacity_max effects_default
    local python_bin
    python_bin="$(terminal_policy_python_bin)"
    fps_default="$(terminal_policy_query 'setting:TINO_TERMINAL_FPS:default')"
    fps_min="$(terminal_policy_query 'setting:TINO_TERMINAL_FPS:min')"
    fps_max="$(terminal_policy_query 'setting:TINO_TERMINAL_FPS:max')"

    opacity_default="$(terminal_policy_query 'setting:TINO_TERMINAL_OPACITY:default')"
    opacity_min="$(terminal_policy_query 'setting:TINO_TERMINAL_OPACITY:min')"
    opacity_max="$(terminal_policy_query 'setting:TINO_TERMINAL_OPACITY:max')"

    effects_default="$(terminal_policy_query 'setting:TINO_TERMINAL_EFFECTS:default')"

    TINO_TERMINAL_FPS="$("$python_bin" - "$fps_default" "$fps_min" "$fps_max" "${TINO_TERMINAL_FPS:-}" <<'PY'
import sys

default, minimum, maximum, raw = sys.argv[1:]
default = int(default)
minimum = int(minimum)
maximum = int(maximum)
try:
    value = int(raw)
except Exception:
    value = default
print(max(minimum, min(maximum, value)))
PY
)"

    TINO_TERMINAL_OPACITY="$("$python_bin" - "$opacity_default" "$opacity_min" "$opacity_max" "${TINO_TERMINAL_OPACITY:-}" <<'PY'
import sys

default, minimum, maximum, raw = sys.argv[1:]
default = float(default)
minimum = float(minimum)
maximum = float(maximum)
try:
    value = float(raw)
except Exception:
    value = default
value = max(minimum, min(maximum, value))
print(f"{value:.2f}")
PY
)"

    TINO_TERMINAL_EFFECTS="$("$python_bin" - "$effects_default" "${TINO_TERMINAL_EFFECTS:-}" "$(terminal_policy_query 'setting:TINO_TERMINAL_EFFECTS:allowed')" <<'PY'
import re
import sys

default, raw, allowed_text = sys.argv[1:]
allowed = {item.strip().lower() for item in allowed_text.splitlines() if item.strip()}
normalized = raw.strip().lower()
if normalized in allowed:
    print(normalized)
elif re.match(r'^(/|\.|~).+', raw.strip()):
    print(raw.strip())
else:
    print(default)
PY
)"

    export TINO_TERMINAL_FPS
    export TINO_TERMINAL_OPACITY
    export TINO_TERMINAL_EFFECTS
}
