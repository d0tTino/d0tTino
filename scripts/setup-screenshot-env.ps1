# Install fastfetch, bottom, Nushell and Zed on Windows using winget.
# If run on Linux or macOS with PowerShell, delegate to the bash script.

$ErrorActionPreference = 'Stop'

if ($IsWindows) {
    $packages = @(
        @{ Id = 'fastfetch.fastfetch' },
        @{ Id = 'Clement.bottom' },
        @{ Id = 'NushellTeam.Nushell' },
        @{ Id = 'ZedIndustries.Zed' }
    )
    foreach ($pkg in $packages) {
        winget install --id $pkg.Id -e --accept-source-agreements --accept-package-agreements
    }
} else {
    $script = Join-Path $PSScriptRoot 'setup-screenshot-env.sh'
    & $script
}

