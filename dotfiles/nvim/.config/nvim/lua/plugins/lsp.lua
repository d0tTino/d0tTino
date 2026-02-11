return {
    {
        "williamboman/mason.nvim",
        cmd = { "Mason", "MasonInstall", "MasonUpdate" },
        opts = {},
    },
    {
        "williamboman/mason-lspconfig.nvim",
        event = { "BufReadPre", "BufNewFile" },
        dependencies = {
            "williamboman/mason.nvim",
            "neovim/nvim-lspconfig",
        },
        opts = {
            ensure_installed = { "lua_ls", "pyright", "ts_ls", "bashls" },
            automatic_installation = true,
        },
        config = function(_, opts)
            require("mason").setup()

            local mason_lspconfig = require("mason-lspconfig")
            mason_lspconfig.setup(opts)

            local lspconfig = require("lspconfig")
            mason_lspconfig.setup_handlers({
                function(server_name)
                    lspconfig[server_name].setup({})
                end,
            })
        end,
    },
}
