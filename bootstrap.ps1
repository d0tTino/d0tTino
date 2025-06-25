param(
    [switch] $InstallWinget
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

