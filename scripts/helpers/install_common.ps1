$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$scripts = Join-Path $repoRoot 'scripts'

param(
    [switch] $Winget,
    [switch] $WindowsTerminal,
    [switch] $InstallWSL,
    [switch] $SetupWSL,
    [switch] $SetupDocker,
    [string] $DockerImageName
)

& "$scripts/fix-path.ps1"
& "$scripts/setup-hooks.ps1"
& "$scripts/helpers/install_fonts.ps1"
& "$scripts/helpers/sync_palettes.ps1"

if ($Winget) { & "$scripts/setup-winget.ps1" }
if ($WindowsTerminal) { & "$scripts/install-windows-terminal.ps1" }
if ($InstallWSL) { & "$scripts/install-wsl.ps1" }
if ($SetupWSL) { & "$scripts/setup-wsl.ps1" }
if ($SetupDocker) {
    $argsList = @()
    if ($DockerImageName) { $argsList += @('-ImageName', $DockerImageName) }
    & "$scripts/setup-docker.ps1" @argsList
}
