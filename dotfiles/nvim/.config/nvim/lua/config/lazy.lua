local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"

if not vim.loop.fs_stat(lazypath) then
    local message = table.concat({
        "lazy.nvim is missing and Neovim startup is running in offline-only mode.",
        "Install it during provisioning and rerun Neovim.",
        "Expected path: " .. lazypath,
        "Bootstrap command: ./scripts/setup-nvim.sh",
    }, "\n")

    vim.schedule(function()
        vim.api.nvim_echo({ { message, "ErrorMsg" } }, true, {})
    end)

    return
end

vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
    spec = {
        { import = "plugins" },
    },
    defaults = {
        lazy = true,
    },
    install = {
        colorscheme = { "nightfox" },
    },
    checker = {
        enabled = false,
    },
})
