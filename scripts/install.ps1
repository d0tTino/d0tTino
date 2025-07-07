$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent

if (-not $IsWindows) {
    & bash (Join-Path $PSScriptRoot 'install.sh')
    return
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error 'winget is required but not installed.'
    exit 1
}

winget install --id NerdFonts.CaskaydiaCove -e --accept-source-agreements --accept-package-agreements

$base = 'https://raw.githubusercontent.com/d0tTino/d0tTino/main/palettes'
$dest = Join-Path $repoRoot 'palettes'
if (-not (Test-Path $dest)) {
    New-Item -ItemType Directory -Path $dest | Out-Null
}
foreach ($name in 'blacklight','dracula','solarized-dark') {
    Invoke-WebRequest -Uri "$base/$name.toml" -OutFile (Join-Path $dest "$name.toml")
}
