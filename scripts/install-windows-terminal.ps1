# Copy Windows Terminal settings into the LocalState folder.
$wtDir = Join-Path $Env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState'
if (-not (Test-Path $wtDir)) {
    New-Item -ItemType Directory -Path $wtDir -Force | Out-Null
}

$repoRoot = Split-Path $PSScriptRoot -Parent

# Render canonical terminal profile overrides when bash is available.
$bash = Get-Command bash -ErrorAction SilentlyContinue
if ($bash) {
    & $bash.Path -lc "`"$HOME/.config/tino/terminal-profile.sh`" windows-terminal `"$repoRoot`""
}

# Regenerate settings from the shared profile template before copying.
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & $python (Join-Path $repoRoot 'windows-terminal/generate_settings.py') `
        (Join-Path $repoRoot 'windows-terminal/settings.base.json') `
        (Join-Path $repoRoot 'windows-terminal/settings.json') `
        --terminal-overrides (Join-Path $repoRoot 'windows-terminal/terminal-profile-overrides.json')
}

$source = Join-Path $repoRoot 'windows-terminal\settings.json'
Copy-Item -Path $source -Destination (Join-Path $wtDir 'settings.json') -Force
Write-Host "Windows Terminal settings copied to $wtDir"
