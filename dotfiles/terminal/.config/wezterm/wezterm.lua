local wezterm = require("wezterm")

return {
    font = wezterm.font_with_fallback({
        "JetBrainsMono Nerd Font",
        "CaskaydiaCove Nerd Font",
    }),
    font_size = 13.0,
    color_scheme = "Tokyo Night",
    window_background_opacity = 0.90,
    max_fps = 165,
    enable_wayland = true,
    use_fancy_tab_bar = false,
    hide_tab_bar_if_only_one_tab = true,
    window_padding = {
        left = 10,
        right = 10,
        top = 8,
        bottom = 8,
    },
}
