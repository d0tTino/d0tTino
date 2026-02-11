#!/usr/bin/env bash
set -euo pipefail

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
config_dir="$config_home/ghostty"
mkdir -p "$config_dir"

template_file="$config_home/tino/ghostty.toml.tmpl"
if [[ ! -f "$template_file" ]]; then
    echo "Missing template: $template_file" >&2
    exit 1
fi

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

printf '%s\n' "$rendered" > "$config_dir/ghostty.toml"
echo "Rendered Ghostty config to $config_dir/ghostty.toml"
