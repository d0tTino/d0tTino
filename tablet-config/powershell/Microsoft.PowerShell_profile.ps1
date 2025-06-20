# Initialize Oh My Posh
$ThemePath = Join-Path $PSScriptRoot "..\oh-my-posh\custom_tokyo.omp.json"
Invoke-Expression (& { (oh-my-posh init powershell --config $ThemePath | Out-String) })

# Initialize Zoxide
Invoke-Expression (& { (zoxide init powershell | Out-String) })