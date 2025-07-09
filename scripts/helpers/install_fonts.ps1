$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    & bash (Join-Path $PSScriptRoot 'install_fonts.sh')
    return
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error 'winget is required but not installed.'
    exit 1
}

winget install --id NerdFonts.CaskaydiaCove -e --accept-source-agreements --accept-package-agreements
