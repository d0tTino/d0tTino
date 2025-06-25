param(
    [switch] $InstallWinget,
    [switch] $InstallWindowsTerminal,
    [switch] $InstallWSL,
    [switch] $SetupWSL
)

& "$PSScriptRoot/scripts/fix-path.ps1"
if ($IsWindows) {
    & "$PSScriptRoot/scripts/setup-hooks.ps1"
} else {
    & bash "$PSScriptRoot/scripts/setup-hooks.sh"
}

if ($InstallWinget -and $IsWindows) {
    & "$PSScriptRoot/scripts/setup-winget.ps1"
}

if ($InstallWindowsTerminal -and $IsWindows) {
    & "$PSScriptRoot/scripts/install-windows-terminal.ps1"
}

if ($InstallWSL -and $IsWindows) {
    & "$PSScriptRoot/scripts/install-wsl.ps1"
}

if ($SetupWSL -and (Get-Command bash -ErrorAction SilentlyContinue)) {
    & bash "$PSScriptRoot/scripts/setup-wsl.sh"
}

