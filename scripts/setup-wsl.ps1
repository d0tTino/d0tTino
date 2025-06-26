$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    & bash (Join-Path $PSScriptRoot 'setup-wsl.sh')
    return
}

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Error 'wsl.exe is required but not installed.'
    exit 1
}

$script = Join-Path $PSScriptRoot 'setup-wsl.sh'
& wsl.exe bash $script
