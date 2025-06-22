# Clean up and persist the user's PATH value
$paths = $Env:Path -split ';'
$unique = @()
$uniqueLower = @()

foreach ($p in $paths) {
    $trim = $p.Trim()
    $norm = $trim -replace '[\\/]+', '\\'
    $norm = $norm.TrimEnd('\', '/')
    $lower = $norm.ToLower()
    if ($norm -and $uniqueLower -notcontains $lower) {
        $unique += $norm
        $uniqueLower += $lower

    }
}

$userProfile = $Env:USERPROFILE
if (-not $userProfile) {
    $userProfile = $Env:HOME
}
if (-not $userProfile) {
    try {
        $userProfile = [Environment]::GetFolderPath('UserProfile')
    } catch {
        $userProfile = $null
    }
}
if ($userProfile) {
    $userBin = Join-Path $userProfile 'bin'
    $userBinLower = $userBin.ToLower()
    if ($uniqueLower -notcontains $userBinLower) {
        $unique += $userBin
        $uniqueLower += $userBinLower

    }
}

$joinedPath = $unique -join ';'
$newPath = $joinedPath
$originalCount = $unique.Count
if ($newPath.Length -gt 1023) {
    Write-Warning "PATH length exceeds 1023 characters and will be truncated."
    $removed = $newPath.Substring(1023)
    Write-Verbose "Removed portion: $removed" -Verbose
    $newPath = $newPath.Substring(0, 1023)

}
$finalCount = ($newPath -split ';').Count
if ($finalCount -lt $originalCount) {
    Write-Warning 'Some PATH entries were dropped due to size limitations.'
}

[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "User PATH updated. Restart your terminal to apply changes."
