local generated = os.getenv("XDG_CONFIG_HOME")
if generated == nil or generated == "" then
    generated = os.getenv("HOME") .. "/.config"
end

local profile = generated .. "/wezterm/wezterm.generated.lua"
local ok, conf = pcall(dofile, profile)
if ok then
    return conf
end

return {
    font_size = 13.0,
}
