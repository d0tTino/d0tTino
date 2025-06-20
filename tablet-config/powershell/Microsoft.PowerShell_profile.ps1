# Initialize Oh My Posh if available
$ThemePath = Join-Path $PSScriptRoot "..\oh-my-posh\custom_tokyo.omp.json"
if (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (oh-my-posh init powershell --config $ThemePath | Out-String) })
}

# Initialize Zoxide if available
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (zoxide init powershell | Out-String) })
}
