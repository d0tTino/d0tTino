param(
    [switch] $InstallWinget,
    [switch] $InstallWindowsTerminal,
    [switch] $InstallWSL,
    [switch] $SetupWSL,
    [switch] $SetupDocker,
    [string] $DockerImageName
)

$argsList = @()
if ($InstallWinget) { $argsList += '--winget' }
if ($InstallWindowsTerminal) { $argsList += '--windows-terminal' }
if ($InstallWSL) { $argsList += '--install-wsl' }
if ($SetupWSL) { $argsList += '--setup-wsl' }
if ($SetupDocker) { $argsList += '--setup-docker' }
if ($DockerImageName) { $argsList += @('--image', $DockerImageName) }

if ($IsWindows) {
    & "$PSScriptRoot/scripts/helpers/install_common.ps1" @argsList
} elseif (Get-Command bash -ErrorAction SilentlyContinue) {
    & bash "$PSScriptRoot/scripts/install_common.sh" @argsList
}
