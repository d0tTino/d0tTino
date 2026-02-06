return {
    {
        "neovim/nvim-lspconfig",
        event = { "BufReadPre", "BufNewFile" },
        ft = { "lua", "python", "javascript", "typescript", "sh" },
        cmd = { "LspInfo", "LspStart" },
        config = function()
            local lspconfig = require("lspconfig")

            local servers = { "lua_ls", "pyright", "ts_ls", "bashls" }
            for _, server in ipairs(servers) do
                if lspconfig[server] then
                    lspconfig[server].setup({})
                end
            end
        end,
    },
}
