# Configure Git to use local hooks directory if not already set.
$ErrorActionPreference = 'Stop'

try {
    $currentPath = git config --get core.hooksPath 2>$null
} catch {
    $currentPath = $null
}

if (-not $currentPath) {
    git config core.hooksPath .githooks
    Write-Host "Git hooks enabled using .githooks"
} else {
    Write-Host "Git hooks already configured at '$currentPath'"
}
