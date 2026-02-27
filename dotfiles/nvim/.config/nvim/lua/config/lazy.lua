local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
local uv = vim.uv or vim.loop

local function env_enabled(name)
    local value = vim.env[name]
    return value == "1" or value == "true" or value == "TRUE"
end

local function notify_missing_lazy(offline_mode)
    local details = {
        "lazy.nvim is missing; plugin setup is skipped to keep startup deterministic.",
        "Expected path: " .. lazypath,
        "Bootstrap command: ./scripts/setup-nvim.sh",
        "Optional runtime bootstrap: TINO_NVIM_AUTO_BOOTSTRAP=1",
    }

    if offline_mode then
        table.insert(details, 2, "Offline mode is enabled via TINO_NVIM_OFFLINE=1.")
    else
        table.insert(details, 2, "Enable auto-bootstrap with TINO_NVIM_AUTO_BOOTSTRAP=1 if network access is allowed.")
    end

    vim.schedule(function()
        vim.api.nvim_echo({ { table.concat(details, "\n"), "ErrorMsg" } }, true, {})
    end)
end

if not uv.fs_stat(lazypath) then
    local auto_bootstrap = env_enabled("TINO_NVIM_AUTO_BOOTSTRAP")
    local offline_mode = env_enabled("TINO_NVIM_OFFLINE")

    if auto_bootstrap and not offline_mode then
        if vim.fn.executable("git") ~= 1 then
            notify_missing_lazy(false)
            return
        end

        vim.fn.mkdir(vim.fn.fnamemodify(lazypath, ":h"), "p")
        local cmd = {
            "git",
            "clone",
            "--filter=blob:none",
            "--branch=stable",
            "https://github.com/folke/lazy.nvim.git",
            lazypath,
        }
        vim.fn.system(cmd)

        if vim.v.shell_error ~= 0 or not uv.fs_stat(lazypath) then
            notify_missing_lazy(false)
            return
        end
    else
        notify_missing_lazy(offline_mode)
        return
    end
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
