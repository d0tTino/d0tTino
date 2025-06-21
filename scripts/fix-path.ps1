# Clean up and persist the user's PATH value
$paths = $Env:Path -split ';'
$list = [System.Collections.Generic.List[string]]::new()
foreach ($p in $paths) {
    $trim = $p.Trim()
    if ($trim -and -not $list.Contains($trim)) {
        $list.Add($trim) | Out-Null
    }
}

$userBin = Join-Path $Env:USERPROFILE 'bin'
if (-not $list.Contains($userBin)) {
    $list.Add($userBin) | Out-Null
}

$newPath = [string]::Join(';', $list)
$maxLength = 1023
while ($newPath.Length -gt $maxLength -and $list.Count -gt 0) {
    $list.RemoveAt(0)
    $newPath = [string]::Join(';', $list)
}

[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "User PATH updated. Restart your terminal to apply changes."
