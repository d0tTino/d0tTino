# Persist the current PATH value at the machine scope
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this script from an elevated PowerShell session."
    exit 1
}

[Environment]::SetEnvironmentVariable('Path', $Env:Path, [EnvironmentVariableTarget]::Machine)
Write-Host "System PATH updated. Restart your terminal to apply changes."
