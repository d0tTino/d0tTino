#!/usr/bin/env bash
set -euo pipefail

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
config_dir="$config_home/wezterm"
mkdir -p "$config_dir"

cat > "$config_dir/wezterm.generated.lua" <<EOC
-- Managed by ~/.config/tino/terminal-profile.sh (provider: wezterm)
local wezterm = require("wezterm")

return {
  font = wezterm.font_with_fallback({"${TINO_TERMINAL_FONT_FAMILY}"}),
  font_size = ${TINO_TERMINAL_FONT_SIZE}.0,
  window_background_opacity = ${TINO_TERMINAL_OPACITY},
  max_fps = ${TINO_TERMINAL_FPS},
  use_fancy_tab_bar = false,
  hide_tab_bar_if_only_one_tab = true,
  window_padding = { left = 10, right = 10, top = 8, bottom = 8 },
  colors = {
    foreground = "${TINO_TERMINAL_FOREGROUND}",
    background = "${TINO_TERMINAL_BACKGROUND}",
    cursor_bg = "${TINO_TERMINAL_CURSOR}",
    cursor_fg = "${TINO_TERMINAL_BACKGROUND}",
    selection_bg = "${TINO_TERMINAL_SELECTION}",
    ansi = {"${TINO_TERMINAL_COLOR_0}", "${TINO_TERMINAL_COLOR_1}", "${TINO_TERMINAL_COLOR_2}", "${TINO_TERMINAL_COLOR_3}", "${TINO_TERMINAL_COLOR_4}", "${TINO_TERMINAL_COLOR_5}", "${TINO_TERMINAL_COLOR_6}", "${TINO_TERMINAL_COLOR_7}"},
    brights = {"${TINO_TERMINAL_COLOR_8}", "${TINO_TERMINAL_COLOR_9}", "${TINO_TERMINAL_COLOR_10}", "${TINO_TERMINAL_COLOR_11}", "${TINO_TERMINAL_COLOR_12}", "${TINO_TERMINAL_COLOR_13}", "${TINO_TERMINAL_COLOR_14}", "${TINO_TERMINAL_COLOR_15}"},
  },
}
EOC

echo "Rendered WezTerm config to $config_dir/wezterm.generated.lua"
