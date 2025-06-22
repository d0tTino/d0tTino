# Copy Windows Terminal settings into the LocalState folder.
$wtDir = Join-Path $Env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState'
if (-not (Test-Path $wtDir)) {
    New-Item -ItemType Directory -Path $wtDir -Force | Out-Null
}
$source = Join-Path $PSScriptRoot '..\windows-terminal\settings.json'
Copy-Item -Path $source -Destination (Join-Path $wtDir 'settings.json') -Force
Write-Host "Windows Terminal settings copied to $wtDir"
