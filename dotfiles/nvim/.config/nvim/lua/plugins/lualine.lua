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
                        a = { bg = "#845CFF", fg = "#000000", gui = "bold" },
                        b = { bg = "#121212", fg = "#f2f2f2" },
                        c = { bg = "#000000", fg = "#f2f2f2" },
                    },
                    insert = {
                        a = { bg = "#66b2ff", fg = "#000000", gui = "bold" },
                    },
                    visual = {
                        a = { bg = "#FC17DA", fg = "#000000", gui = "bold" },
                    },
                    replace = {
                        a = { bg = "#ff66c4", fg = "#000000", gui = "bold" },
                    },
                    command = {
                        a = { bg = "#b2ff59", fg = "#000000", gui = "bold" },
                    },
                    inactive = {
                        a = { bg = "#121212", fg = "#666666" },
                        b = { bg = "#121212", fg = "#666666" },
                        c = { bg = "#000000", fg = "#666666" },
                    },
                },
            },
        },
    },
}
