return {
    {
        "EdenEast/nightfox.nvim",
        lazy = false,
        priority = 1000,
        config = function()
            -- Blacklight palette source of truth lives in terminal layer configs
            -- (ghostty/tmux, and starship when present) to avoid theme drift.
            local blacklight = {
                bg = "#000000",
                fg = "#f2f2f2",
                gray = "#666666",
                pink = "#ff66c4",
                green = "#b2ff59",
                yellow = "#ffff66",
                blue = "#66b2ff",
                purple = "#845CFF",
                cyan = "#66fff2",
                magenta = "#FC17DA",
                white = "#ffffff",
            }

            require("nightfox").setup({
                options = {
                    transparent = false,
                },
                palettes = {
                    nightfox = {
                        bg1 = blacklight.bg,
                        bg0 = blacklight.bg,
                        bg3 = "#121212",
                        sel0 = "#1a1a1a",
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
