param(
    [switch] $InstallWinget
)

& "$PSScriptRoot/scripts/fix-path.ps1"

if ($InstallWinget -and $IsWindows) {
    & "$PSScriptRoot/scripts/setup-winget.ps1"
}

