$ErrorActionPreference = 'Stop'

param(
    [string] $Name = 'QuickVM',
    [switch] $QuickCreate,
    [int] $MemoryGB = 4
)

if (-not $IsWindows) {
    return
}

if (-not (Get-Command New-VM -ErrorAction SilentlyContinue)) {
    Write-Error 'Hyper-V is required but not installed.'
    exit 1
}

if ($QuickCreate) {
    Start-Process 'virtmgmt.msc' '-quick-create'
    return
}

$VhdPath = Join-Path $env:PUBLIC "Documents\\Hyper-V\\$Name.vhdx"
New-VM -Name $Name -MemoryStartupBytes ($MemoryGB * 1GB) -Generation 2 -SwitchName 'Default Switch' -NewVHDPath $VhdPath -NewVHDSizeBytes 60GB | Out-Null

