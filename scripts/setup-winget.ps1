# Install basic command-line tools on Windows using winget.
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    return
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error 'winget is required but not installed.'
    exit 1
}

$packages = @(
    @{ Id = 'ajeetdsouza.zoxide' },
    @{ Id = 'junegunn.fzf' },
    @{ Id = 'sharkdp.bat' },
    @{ Id = 'dandavison.delta' },
    @{ Id = 'Starship.Starship' },
    @{ Id = 'Microsoft.WindowsTerminal' },
    @{ Id = 'Microsoft.OpenSSH.Preview' }
)

foreach ($pkg in $packages) {
    winget install --id $pkg.Id -e --accept-source-agreements --accept-package-agreements
}
