#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$success = $true

try {
    Write-Host "Measuring PowerShell startup..."
    $time = (Measure-Command { pwsh -NoLogo -NoProfile -Command 'exit' }).TotalMilliseconds
    Write-Host "pwsh startup: $time ms"
} catch {
    Write-Error "pwsh failed: $_"
    $success = $false
}

try {
    Write-Host "Running zoxide query..."
    $result = zoxide query ~
    Write-Host "zoxide query ~ => $result"
} catch {
    Write-Error "zoxide query failed: $_"
    $success = $false
}

try {
    Write-Host "Checking git diff..."
    git diff --stat
} catch {
    Write-Error "git diff failed: $_"
    $success = $false
}

if ($success) {
    Write-Host "Smoke test completed successfully."
    exit 0
} else {
    Write-Error "Smoke test failed."
    exit 1
}
