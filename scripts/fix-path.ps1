# Clean up and persist the user's PATH value
$paths = $Env:Path -split ';'
$unique = @()
$uniqueLower = @()

foreach ($p in $paths) {
    $trim = $p.Trim()
    if (-not $trim) { continue }

    $lower = $trim.ToLower()
    if ($uniqueLower -notcontains $lower) {
        $unique += $trim
        $uniqueLower += $lower
    }
}

$userBin = Join-Path $Env:USERPROFILE 'bin'
$userBinLower = $userBin.ToLower()
if ($uniqueLower -notcontains $userBinLower) {
    $unique += $userBin
    $uniqueLower += $userBinLower
}

$newPath = $unique -join ';'
if ($newPath.Length -gt 1023) {
    $newPath = $newPath.Substring(0, 1023)
}

[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "User PATH updated. Restart your terminal to apply changes."
