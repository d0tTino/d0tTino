$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$scripts = Join-Path $repoRoot 'scripts'

& "$scripts/setup-hooks.ps1"
& "$scripts/helpers/install_fonts.ps1"
& "$scripts/helpers/sync_palettes.ps1"
