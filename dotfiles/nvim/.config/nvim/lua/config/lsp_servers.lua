local M = {}

local function module_dir()
    local source = debug.getinfo(1, "S").source
    local path = source:sub(2)
    return vim.fn.fnamemodify(path, ":h")
end

local function load_servers()
    local servers_path = module_dir() .. "/../../lsp_servers.txt"
    local lines = vim.fn.readfile(servers_path)
    local servers = {}

    for _, line in ipairs(lines) do
        local server = vim.trim(line)
        if server ~= "" then
            table.insert(servers, server)
        end
    end

    return servers
end

M.servers = load_servers()

return M
