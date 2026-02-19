#!/usr/bin/env bash
set -euo pipefail
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
config_dir="$config_home/kitty"
mkdir -p "$config_dir"

kitty_fps="${TINO_TERMINAL_FPS}"
if [[ "$kitty_fps" -lt 1 ]]; then
    kitty_fps=1
fi
kitty_repaint_delay_ms=$(( (1000 + kitty_fps - 1) / kitty_fps ))

cat > "$config_dir/kitty.conf" <<EOC
# Managed by ~/.config/tino/terminal-profile.sh (provider: kitty)
font_family ${TINO_TERMINAL_FONT_FAMILY}
font_size ${TINO_TERMINAL_FONT_SIZE}
background_opacity ${TINO_TERMINAL_OPACITY}
sync_to_monitor yes
repaint_delay ${kitty_repaint_delay_ms}
# tino-contract:unsupported TINO_TERMINAL_EFFECTS
foreground ${TINO_TERMINAL_FOREGROUND}
background ${TINO_TERMINAL_BACKGROUND}
cursor ${TINO_TERMINAL_CURSOR}
selection_background ${TINO_TERMINAL_SELECTION}
color0 ${TINO_TERMINAL_COLOR_0}
color1 ${TINO_TERMINAL_COLOR_1}
color2 ${TINO_TERMINAL_COLOR_2}
color3 ${TINO_TERMINAL_COLOR_3}
color4 ${TINO_TERMINAL_COLOR_4}
color5 ${TINO_TERMINAL_COLOR_5}
color6 ${TINO_TERMINAL_COLOR_6}
color7 ${TINO_TERMINAL_COLOR_7}
color8 ${TINO_TERMINAL_COLOR_8}
color9 ${TINO_TERMINAL_COLOR_9}
color10 ${TINO_TERMINAL_COLOR_10}
color11 ${TINO_TERMINAL_COLOR_11}
color12 ${TINO_TERMINAL_COLOR_12}
color13 ${TINO_TERMINAL_COLOR_13}
color14 ${TINO_TERMINAL_COLOR_14}
color15 ${TINO_TERMINAL_COLOR_15}
EOC
echo "Rendered kitty config to $config_dir/kitty.conf"
