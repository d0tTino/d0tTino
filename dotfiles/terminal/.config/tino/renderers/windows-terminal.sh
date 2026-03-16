#!/usr/bin/env bash
set -euo pipefail
repo_root="${1:-}"
if [[ -z "$repo_root" ]]; then
    echo "windows-terminal renderer requires repo root path" >&2
    exit 1
fi

acrylic_enabled="false"
resolved_opacity="1.0"
opacity="${TINO_TERMINAL_OPACITY}"

opacity_is_translucent="false"
if awk -v value="$opacity" 'BEGIN { exit !(value < 1.0) }'; then
    opacity_is_translucent="true"
fi

acrylic_supported="true"
case "${TINO_WINDOWS_TERMINAL_ACRYLIC_SUPPORTED:-true}" in
    false|False|FALSE|no|No|NO|0)
        acrylic_supported="false"
        ;;
esac

effects_enabled="true"
case "${TINO_TERMINAL_EFFECTS,,}" in
    off|false|no|0|none)
        effects_enabled="false"
        ;;
esac

if [[ "$opacity_is_translucent" == "true" && "$effects_enabled" == "true" && "$acrylic_supported" == "true" ]]; then
    acrylic_enabled="true"
    resolved_opacity="$opacity"
fi

output="$repo_root/windows-terminal/terminal-profile-overrides.json"
mkdir -p "$(dirname "$output")"
cat > "$output" <<EOC
{
  "rendering.graphicsAPI": "automatic",
  "profiles": {
    "defaults": {
      "font": {
        "face": "${TINO_TERMINAL_FONT_FAMILY}",
        "size": ${TINO_TERMINAL_FONT_SIZE}
      },
      "useAcrylic": ${acrylic_enabled},
      "acrylicOpacity": ${resolved_opacity},
      "colorScheme": "Blacklight"
    }
  },
  "schemes": [
    {
      "name": "Blacklight",
      "black": "${TINO_TERMINAL_COLOR_0}",
      "red": "${TINO_TERMINAL_COLOR_1}",
      "green": "${TINO_TERMINAL_COLOR_2}",
      "yellow": "${TINO_TERMINAL_COLOR_3}",
      "blue": "${TINO_TERMINAL_COLOR_4}",
      "purple": "${TINO_TERMINAL_COLOR_5}",
      "cyan": "${TINO_TERMINAL_COLOR_6}",
      "white": "${TINO_TERMINAL_COLOR_7}",
      "brightBlack": "${TINO_TERMINAL_COLOR_8}",
      "brightRed": "${TINO_TERMINAL_COLOR_9}",
      "brightGreen": "${TINO_TERMINAL_COLOR_10}",
      "brightYellow": "${TINO_TERMINAL_COLOR_11}",
      "brightBlue": "${TINO_TERMINAL_COLOR_12}",
      "brightPurple": "${TINO_TERMINAL_COLOR_13}",
      "brightCyan": "${TINO_TERMINAL_COLOR_14}",
      "brightWhite": "${TINO_TERMINAL_COLOR_15}",
      "background": "${TINO_TERMINAL_BACKGROUND}",
      "foreground": "${TINO_TERMINAL_FOREGROUND}",
      "cursorColor": "${TINO_TERMINAL_CURSOR}",
      "selectionBackground": "${TINO_TERMINAL_SELECTION}"
    }
  ],
  "tinoContract": {
    "unsupported": {
      "TINO_TERMINAL_FPS": "windows-terminal has no profile-level refresh/fps override; retained as no-op",
      "TINO_WINDOWS_TERMINAL_ACRYLIC_SUPPORTED": "set false to force deterministic fallback (opaque background, useAcrylic=false) on unsupported environments",
      "rendering.graphicsAPI": "older schema/runtime combinations may ignore this setting; generator falls back to base settings without it when schema is unrecognized"
    }
  }
}
EOC
echo "Rendered Windows Terminal overrides to $output"
