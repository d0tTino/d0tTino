param(
    [switch] $InstallWinget
)

& "$PSScriptRoot/scripts/fix-path.ps1"
& bash "$PSScriptRoot/scripts/setup-hooks.sh"

if ($InstallWinget -and $IsWindows) {
    & "$PSScriptRoot/scripts/setup-winget.ps1"
}

