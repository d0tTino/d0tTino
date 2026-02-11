local palette = require("config.palette")

return {
    {
        "nvim-lualine/lualine.nvim",
        event = "VeryLazy",
        dependencies = {
            "nvim-tree/nvim-web-devicons",
        },
        opts = {
            options = {
                globalstatus = true,
                theme = {
                    normal = {
                        a = { bg = palette.purple, fg = palette.bg, gui = "bold" },
                        b = { bg = palette.bg_alt, fg = palette.fg },
                        c = { bg = palette.bg, fg = palette.fg },
                    },
                    insert = {
                        a = { bg = palette.blue, fg = palette.bg, gui = "bold" },
                    },
                    visual = {
                        a = { bg = palette.magenta, fg = palette.bg, gui = "bold" },
                    },
                    replace = {
                        a = { bg = palette.pink, fg = palette.bg, gui = "bold" },
                    },
                    command = {
                        a = { bg = palette.green, fg = palette.bg, gui = "bold" },
                    },
                    inactive = {
                        a = { bg = palette.bg_alt, fg = palette.gray },
                        b = { bg = palette.bg_alt, fg = palette.gray },
                        c = { bg = palette.bg, fg = palette.gray },
                    },
                },
            },
        },
    },
}
