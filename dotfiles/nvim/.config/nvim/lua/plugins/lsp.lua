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
            automatic_installation = false,
        },
        config = function(_, opts)
            require("mason").setup()

            local mason_lspconfig = require("mason-lspconfig")
            mason_lspconfig.setup(opts)

            local lspconfig = require("lspconfig")
            local required_servers = { "lua_ls", "pyright", "ts_ls", "bashls" }
            local installed_servers = mason_lspconfig.get_installed_servers()
            local installed_lookup = {}
            local missing_servers = {}

            for _, server in ipairs(installed_servers) do
                installed_lookup[server] = true
            end

            for _, server in ipairs(required_servers) do
                if installed_lookup[server] then
                    lspconfig[server].setup({})
                else
                    table.insert(missing_servers, server)
                end
            end

            if #missing_servers > 0 then
                vim.schedule(function()
                    vim.notify(
                        "Missing Mason LSP servers: "
                            .. table.concat(missing_servers, ", ")
                            .. ". Run ./scripts/setup-nvim.sh to provision them.",
                        vim.log.levels.WARN
                    )
                end)
            end
        end,
    },
}
