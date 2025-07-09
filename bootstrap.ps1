param(
    [switch] $InstallWinget,
    [switch] $InstallWindowsTerminal,
    [switch] $InstallWSL,
    [switch] $SetupWSL,
    [switch] $SetupDocker,
    [string] $DockerImageName
)

& "$PSScriptRoot/scripts/fix-path.ps1"

if ($IsWindows) {
    & "$PSScriptRoot/scripts/helpers/install_common.ps1"
} elseif (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash "$PSScriptRoot/scripts/install_common.sh"
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

if ($SetupWSL) {
    if ($IsWindows) {
        & "$PSScriptRoot/scripts/setup-wsl.ps1"
    } elseif (Get-Command bash -ErrorAction SilentlyContinue) {
        & bash "$PSScriptRoot/scripts/setup-wsl.sh"
    }
}

if ($SetupDocker) {
    if ($IsWindows) {
        $argsList = @()
        if ($DockerImageName) { $argsList += @('-ImageName', $DockerImageName) }
        & "$PSScriptRoot/scripts/setup-docker.ps1" @argsList
    } elseif (Get-Command bash -ErrorAction SilentlyContinue) {
        $bashArgs = @()
        if ($DockerImageName) { $bashArgs += @('--image', $DockerImageName) }
        & bash "$PSScriptRoot/scripts/setup-docker.sh" @bashArgs
    }
}
