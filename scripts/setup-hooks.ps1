# Configure Git to use local hooks directory if not already set.
$ErrorActionPreference = 'Stop'

try {
    $currentPath = git config --get core.hooksPath 2>$null
} catch {
    $currentPath = $null
}

if (-not $currentPath) {
    git config core.hooksPath .githooks
    try {
        $verifyPath = git config --get core.hooksPath 2>$null
    } catch {
        $verifyPath = $null
    }
    if ($verifyPath -ne '.githooks') {
        Write-Error 'core.hooksPath verification failed'
        exit 1
    }
    Write-Host "Git hooks enabled using .githooks"
} else {
    Write-Host "Git hooks already configured at '$currentPath'"
}
