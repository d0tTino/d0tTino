local generated = os.getenv("XDG_CONFIG_HOME")
if generated == nil or generated == "" then
    generated = os.getenv("HOME") .. "/.config"
end

local profile = generated .. "/wezterm/wezterm.generated.lua"
local ok, conf = pcall(dofile, profile)
if ok then
    -- Authoritative terminal profile rendered by terminal-profile.sh.
    return conf
end

local wezterm = require("wezterm")

-- Safe baseline fallback when wezterm.generated.lua is unavailable.
return {
    font = wezterm.font_with_fallback({
        "CaskaydiaCove Nerd Font",
        "JetBrains Mono",
        "FiraCode Nerd Font",
        "Noto Color Emoji",
    }),
    font_size = 13.0,
    window_background_opacity = 0.92,
    use_fancy_tab_bar = false,
    hide_tab_bar_if_only_one_tab = true,
    window_padding = { left = 10, right = 10, top = 8, bottom = 8 },
    colors = {
        foreground = "#f2f2f2",
        background = "#000000",
        cursor_bg = "#FC17DA",
        cursor_fg = "#000000",
        selection_bg = "#301050",
        ansi = { "#000000", "#ff66c4", "#b2ff59", "#ffff66", "#66b2ff", "#845CFF", "#66fff2", "#f2f2f2" },
        brights = { "#666666", "#ff66c4", "#b2ff59", "#ffff66", "#66b2ff", "#FC17DA", "#66fff2", "#ffffff" },
    },
}
