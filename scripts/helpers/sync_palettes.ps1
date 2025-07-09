$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent
$base = 'https://raw.githubusercontent.com/d0tTino/d0tTino/main/palettes'
$dest = Join-Path $repoRoot 'palettes'
if (-not (Test-Path $dest)) {
    New-Item -ItemType Directory -Path $dest | Out-Null
}
foreach ($name in 'blacklight','dracula','solarized-dark') {
    Invoke-WebRequest -Uri "$base/$name.toml" -OutFile (Join-Path $dest "$name.toml")
}
