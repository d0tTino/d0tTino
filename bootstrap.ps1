param(
    [switch] $InstallWinget
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

