$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    & bash (Join-Path $PSScriptRoot 'install.sh')
    return
}

& "$PSScriptRoot/helpers/install_fonts.ps1"
& "$PSScriptRoot/helpers/sync_palettes.ps1"
& "$PSScriptRoot/setup-hooks.ps1"
