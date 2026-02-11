$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
python "$repoRoot/scripts/helpers/generate_palette_artifacts.py"
python "$repoRoot/windows-terminal/generate_settings.py" "$repoRoot/windows-terminal/settings.base.json" "$repoRoot/windows-terminal/settings.json"
