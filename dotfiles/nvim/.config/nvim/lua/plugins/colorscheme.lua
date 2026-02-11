return {
    {
        "EdenEast/nightfox.nvim",
        lazy = false,
        priority = 1000,
        config = function()
            local blacklight = require("config.palette")

            require("nightfox").setup({
                options = {
                    transparent = false,
                },
                palettes = {
                    nightfox = {
                        bg1 = blacklight.bg,
                        bg0 = blacklight.bg,
                        bg3 = blacklight.bg_alt,
                        sel0 = blacklight.bg_select,
                        fg1 = blacklight.fg,
                        fg0 = blacklight.white,
                        comment = blacklight.gray,
                        blue = blacklight.blue,
                        cyan = blacklight.cyan,
                        green = blacklight.green,
                        magenta = blacklight.magenta,
                        pink = blacklight.pink,
                        red = blacklight.pink,
                        yellow = blacklight.yellow,
                        orange = blacklight.purple,
                    },
                },
            })

            vim.cmd.colorscheme("nightfox")
            require("config.theme_overrides").apply(blacklight)
        end,
    },
}
