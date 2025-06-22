# Export installed packages list using winget
try {
    winget export -o "winget-packages.json" --accept-source-agreements
} catch {
    Write-Error "winget export failed: $_"
    exit 1
}
