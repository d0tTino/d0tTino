local M = {}

function M.apply(palette)
    vim.api.nvim_set_hl(0, "CursorLine", { bg = "#121212" })
    vim.api.nvim_set_hl(0, "CursorLineNr", { fg = palette.yellow, bold = true })

    vim.api.nvim_set_hl(0, "DiagnosticError", { fg = palette.pink })
    vim.api.nvim_set_hl(0, "DiagnosticWarn", { fg = palette.yellow })
    vim.api.nvim_set_hl(0, "DiagnosticInfo", { fg = palette.blue })
    vim.api.nvim_set_hl(0, "DiagnosticHint", { fg = palette.cyan })

    vim.api.nvim_set_hl(0, "DiagnosticVirtualTextError", { fg = palette.pink, bg = "#1a0f16" })
    vim.api.nvim_set_hl(0, "DiagnosticVirtualTextWarn", { fg = palette.yellow, bg = "#1a1a0f" })
    vim.api.nvim_set_hl(0, "DiagnosticVirtualTextInfo", { fg = palette.blue, bg = "#0f141a" })
    vim.api.nvim_set_hl(0, "DiagnosticVirtualTextHint", { fg = palette.cyan, bg = "#0f1a1a" })
end

return M
