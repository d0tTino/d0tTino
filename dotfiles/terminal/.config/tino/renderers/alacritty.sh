#!/usr/bin/env bash
set -euo pipefail
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
config_dir="$config_home/alacritty"
mkdir -p "$config_dir"
cat > "$config_dir/alacritty.toml" <<EOC
# Managed by ~/.config/tino/terminal-profile.sh (provider: alacritty)
# tino-contract:unsupported TINO_TERMINAL_FPS
# tino-contract:unsupported TINO_TERMINAL_EFFECTS
[font]
size = ${TINO_TERMINAL_FONT_SIZE}
normal = { family = "${TINO_TERMINAL_FONT_FAMILY}", style = "Regular" }

[window]
opacity = ${TINO_TERMINAL_OPACITY}

[colors.primary]
background = "${TINO_TERMINAL_BACKGROUND}"
foreground = "${TINO_TERMINAL_FOREGROUND}"

[colors.cursor]
cursor = "${TINO_TERMINAL_CURSOR}"

[colors.selection]
background = "${TINO_TERMINAL_SELECTION}"

[colors.normal]
black = "${TINO_TERMINAL_COLOR_0}"
red = "${TINO_TERMINAL_COLOR_1}"
green = "${TINO_TERMINAL_COLOR_2}"
yellow = "${TINO_TERMINAL_COLOR_3}"
blue = "${TINO_TERMINAL_COLOR_4}"
magenta = "${TINO_TERMINAL_COLOR_5}"
cyan = "${TINO_TERMINAL_COLOR_6}"
white = "${TINO_TERMINAL_COLOR_7}"

[colors.bright]
black = "${TINO_TERMINAL_COLOR_8}"
red = "${TINO_TERMINAL_COLOR_9}"
green = "${TINO_TERMINAL_COLOR_10}"
yellow = "${TINO_TERMINAL_COLOR_11}"
blue = "${TINO_TERMINAL_COLOR_12}"
magenta = "${TINO_TERMINAL_COLOR_13}"
cyan = "${TINO_TERMINAL_COLOR_14}"
white = "${TINO_TERMINAL_COLOR_15}"
EOC
echo "Rendered Alacritty config to $config_dir/alacritty.toml"
