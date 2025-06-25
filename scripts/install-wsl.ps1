$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    return
}

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Error 'wsl.exe is required but not installed.'
    exit 1
}

$featuresCmd = Get-Command Get-WindowsOptionalFeature -ErrorAction SilentlyContinue
if ($featuresCmd) {
    $features = @(
        'Microsoft-Windows-Subsystem-Linux'
        'VirtualMachinePlatform'
    )
    foreach ($feature in $features) {
        try {
            $info = Get-WindowsOptionalFeature -Online -FeatureName $feature
            if ($info.State -ne 'Enabled') {
                Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName $feature | Out-Null
            }
        } catch {
            Write-Warning "Failed to check or enable feature $feature: $_"
        }
    }
}

wsl --install
