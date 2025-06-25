param(
    [switch] $InstallWinget,
    [switch] $InstallWindowsTerminal,
    [switch] $SetupWSL
)

& "$PSScriptRoot/scripts/fix-path.ps1"
if (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash "$PSScriptRoot/scripts/setup-hooks.sh"
} else {
    & "$PSScriptRoot/scripts/setup-hooks.ps1"
}

if ($InstallWinget -and $IsWindows) {
    & "$PSScriptRoot/scripts/setup-winget.ps1"
}

if ($InstallWindowsTerminal -and $IsWindows) {
    & "$PSScriptRoot/scripts/install-windows-terminal.ps1"
}

if ($SetupWSL -and (Get-Command bash -ErrorAction SilentlyContinue)) {
    & bash "$PSScriptRoot/scripts/setup-wsl.sh"
}

