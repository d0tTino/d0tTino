# Clean up and persist the user's PATH value
$paths = $Env:Path -split ';'
$unique = @()

foreach ($p in $paths) {
    $trim = $p.Trim()
    if ($trim -and $unique -notcontains $trim) {
        $unique += $trim
    }
}

$userBin = Join-Path $Env:USERPROFILE 'bin'
if ($unique -notcontains $userBin) {
    $unique += $userBin
}

$newPath = $unique -join ';'
if ($newPath.Length -gt 1023) {
    $newPath = $newPath.Substring(0, 1023)
}

[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "User PATH updated. Restart your terminal to apply changes."
