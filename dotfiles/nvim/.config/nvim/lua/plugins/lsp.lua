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
            local lsp_attach_group = vim.api.nvim_create_augroup("UserLspAttachKeymaps", { clear = true })

            vim.api.nvim_create_autocmd("LspAttach", {
                group = lsp_attach_group,
                callback = function(event)
                    local bufnr = event.buf
                    local client = vim.lsp.get_client_by_id(event.data.client_id)

                    if not client then
                        return
                    end

                    local map = function(mode, lhs, rhs, desc)
                        vim.keymap.set(mode, lhs, rhs, {
                            buffer = bufnr,
                            noremap = true,
                            silent = true,
                            desc = desc,
                        })
                    end

                    map("n", "gd", vim.lsp.buf.definition, "LSP: Go to definition")
                    map("n", "gr", vim.lsp.buf.references, "LSP: List references")

                    if client:supports_method("textDocument/codeAction") then
                        map("n", "<leader>ca", vim.lsp.buf.code_action, "LSP: Code action")
                    end

                    if client:supports_method("textDocument/rename") then
                        map("n", "<leader>rn", vim.lsp.buf.rename, "LSP: Rename symbol")
                    end

                    map("n", "<leader>e", vim.diagnostic.open_float, "Diagnostics: Open float")
                end,
            })

            local required_servers = require("config.lsp_servers").servers
            local installed_servers = mason_lspconfig.get_installed_servers()
            local installed_lookup = {}
            local missing_servers = {}
            local capabilities = vim.lsp.protocol.make_client_capabilities()

            local cmp_nvim_lsp_ok, cmp_nvim_lsp = pcall(require, "cmp_nvim_lsp")
            if cmp_nvim_lsp_ok then
                capabilities = cmp_nvim_lsp.default_capabilities(capabilities)
            end

            for _, server in ipairs(installed_servers) do
                installed_lookup[server] = true
            end

            for _, server in ipairs(required_servers) do
                if installed_lookup[server] then
                    lspconfig[server].setup({
                        capabilities = capabilities,
                    })
                else
                    table.insert(missing_servers, server)
                end
            end

            if #missing_servers > 0 then
                vim.schedule(function()
                    vim.notify(
                        "Missing Mason LSP servers: "
                            .. table.concat(missing_servers, ", ")
                            .. ". Run ./scripts/setup-nvim.sh (canonical provisioning flow) to provision them.",
                        vim.log.levels.WARN
                    )
                end)
            end
        end,
    },
}
