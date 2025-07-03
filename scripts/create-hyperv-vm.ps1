$ErrorActionPreference = 'Stop'

param(
    [string] $Name = 'QuickVM',
    [switch] $QuickCreate,
    [int] $MemoryGB = 4,
    [string] $IsoUrl,
    [string] $CloudInit
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

if ($IsoUrl) {
    $isoName = Split-Path $IsoUrl -Leaf
    $isoPath = Join-Path $env:TEMP $isoName
    Invoke-WebRequest -Uri $IsoUrl -OutFile $isoPath
    Add-VMDvdDrive -VMName $Name -Path $isoPath | Out-Null
}

if ($CloudInit) {
    $cloudInitPath = Resolve-Path $CloudInit
    Add-VMDvdDrive -VMName $Name -Path $cloudInitPath | Out-Null
}


