#!/usr/bin/env bash
set -euo pipefail

lazy_path="${XDG_DATA_HOME:-$HOME/.local/share}/nvim/lazy/lazy.nvim"
lazy_repo="https://github.com/folke/lazy.nvim.git"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
lsp_servers_file="$repo_root/dotfiles/nvim/.config/nvim/lsp_servers.txt"
minimum_nvim_version="0.8"
benchmark_script="$repo_root/scripts/benchmark_nvim_startup.sh"
lockfile_check_script="$repo_root/scripts/check-nvim-lockfile.py"
benchmark_startup="${TINO_NVIM_BENCHMARK_STARTUP:-0}"
benchmark_threshold="${TINO_NVIM_MAX_STARTUP_MS:-}"
benchmark_profile_default_threshold="${TINO_NVIM_PROFILE_DEFAULT_MAX_STARTUP_MS:-}"
refresh_lockfile=0

lazy_lock_and_plugins_in_sync() {
    local sync_check
    sync_check="$(nvim --headless +'lua <<"EOF"\
local ok_config, config = pcall(require, "lazy.core.config")\
local ok_lock, lock = pcall(require, "lazy.core.lock")\
if not (ok_config and ok_lock) then\
  vim.cmd("cquit 1")\
end\
\
local locked = lock.load()\
if type(locked) ~= "table" then\
  vim.cmd("cquit 1")\
end\
\
for name, plugin in pairs(config.plugins) do\
  if plugin._ and plugin._.installed and not locked[name] then\
    vim.cmd("cquit 1")\
  end\
end\
\
for name, pin in pairs(locked) do\
  local plugin = config.plugins[name]\
  if not plugin or vim.fn.isdirectory(plugin.dir) == 0 then\
    vim.cmd("cquit 1")\
  end\
\
  local head = vim.fn.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" })\
  if vim.v.shell_error ~= 0 then\
    vim.cmd("cquit 1")\
  end\
\
  head = (head:gsub("%s+", ""))\
  if pin.commit ~= head then\
    vim.cmd("cquit 1")\
  end\
end\
\
print("in-sync")\
vim.cmd("qa!")\
EOF' +qa 2>/dev/null || true)"

    [[ "$sync_check" == *"in-sync"* ]]
}

get_installed_mason_servers() {
    nvim --headless +'lua <<"EOF"\
local ok_registry, registry = pcall(require, "mason-registry")\
if not ok_registry then\
  vim.cmd("cquit 1")\
end\
\
for _, package in ipairs(registry.get_installed_packages()) do\
  print(package.name)\
end\
\
vim.cmd("qa!")\
EOF' +qa
}

for arg in "$@"; do
    case "$arg" in
        --refresh-lockfile)
            refresh_lockfile=1
            ;;
        *)
            echo "Error: unknown argument: $arg" >&2
            echo "Usage: ./scripts/setup-nvim.sh [--refresh-lockfile]" >&2
            exit 1
            ;;
    esac
done

version_gte() {
    local current="$1"
    local minimum="$2"
    [[ "$(printf '%s\n%s\n' "$minimum" "$current" | sort -V | head -n1)" == "$minimum" ]]
}

if [[ ! -f "$lsp_servers_file" ]]; then
    echo "Error: expected canonical LSP server inventory at $lsp_servers_file" >&2
    exit 1
fi

mapfile -t required_lsp_servers < <(sed -e 's/#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$lsp_servers_file" | awk 'NF')
if [[ ${#required_lsp_servers[@]} -eq 0 ]]; then
    echo "Error: no LSP servers were defined in $lsp_servers_file" >&2
    exit 1
fi

if ! command -v nvim >/dev/null 2>&1; then
    echo "Error: nvim is required for Neovim provisioning." >&2
    exit 1
fi

nvim_version_line="$(nvim --version | head -n1)"
if [[ "$nvim_version_line" =~ v([0-9]+\.[0-9]+(\.[0-9]+)?) ]]; then
    nvim_version="${BASH_REMATCH[1]}"
else
    echo "Error: could not parse Neovim version from: $nvim_version_line" >&2
    exit 1
fi

if ! version_gte "$nvim_version" "$minimum_nvim_version"; then
    echo "Error: Neovim $minimum_nvim_version+ is required for setup-nvim.sh (found $nvim_version)." >&2
    exit 1
fi

if [[ -d "$lazy_path/.git" ]]; then
    echo "lazy.nvim already installed at $lazy_path"
elif [[ -e "$lazy_path" ]]; then
    echo "Error: $lazy_path exists but is not a lazy.nvim git checkout." >&2
    exit 1
else
    mkdir -p "$(dirname "$lazy_path")"
    git clone --filter=blob:none --branch=stable "$lazy_repo" "$lazy_path"
    echo "Installed lazy.nvim to $lazy_path"
fi

if [[ "$refresh_lockfile" == "1" ]]; then
    echo "Refreshing Neovim lockfile (intentional plugin upgrade path)..."
    nvim --headless "+Lazy! update" "+Lazy! lock" +qa
    if [[ -f "$lockfile_check_script" ]]; then
        python "$lockfile_check_script"
    else
        echo "Warning: lockfile coverage checker not found at $lockfile_check_script" >&2
    fi
    echo "Lockfile refresh complete. Commit dotfiles/nvim/.config/nvim/lazy-lock.json for deterministic installs."
else
    if lazy_lock_and_plugins_in_sync; then
        echo "Neovim plugins already match lazy-lock.json; skipping plugin sync."
    else
        echo "Plugin state differs from lazy-lock.json; restoring pinned plugin state (headless)..."
        nvim --headless "+Lazy! restore" +qa
    fi
fi

declare -a installed_mason_servers=()
if mapfile -t installed_mason_servers < <(get_installed_mason_servers); then
    declare -A installed_mason_set=()
    for server in "${installed_mason_servers[@]}"; do
        installed_mason_set["$server"]=1
    done

    missing_lsp_servers=()
    for server in "${required_lsp_servers[@]}"; do
        if [[ -z "${installed_mason_set[$server]+x}" ]]; then
            missing_lsp_servers+=("$server")
        fi
    done
else
    echo "Warning: could not query installed Mason packages; installing the canonical server set." >&2
    missing_lsp_servers=("${required_lsp_servers[@]}")
fi

if [[ ${#missing_lsp_servers[@]} -eq 0 ]]; then
    echo "All Mason LSP servers from lsp_servers.txt are already installed; skipping MasonInstall."
else
    echo "Installing missing Mason LSP servers (headless): ${missing_lsp_servers[*]}"
    nvim --headless "+MasonInstall ${missing_lsp_servers[*]}" +qa
fi

if [[ "$benchmark_startup" == "1" ]]; then
    if [[ -f "$benchmark_script" ]]; then
        effective_benchmark_threshold="$benchmark_threshold"
        if [[ -z "$effective_benchmark_threshold" && -n "$benchmark_profile_default_threshold" ]]; then
            effective_benchmark_threshold="$benchmark_profile_default_threshold"
        fi

        echo "Running startup benchmark (TINO_NVIM_BENCHMARK_STARTUP=1)..."
        if [[ -n "$effective_benchmark_threshold" ]]; then
            TINO_NVIM_MAX_STARTUP_MS="$effective_benchmark_threshold" bash "$benchmark_script"
        else
            bash "$benchmark_script"
        fi
    else
        echo "Warning: benchmark script not found at $benchmark_script" >&2
    fi
fi

echo "Neovim provisioning complete."
