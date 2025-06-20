# Initialize Oh My Posh
Invoke-Expression (& { (oh-my-posh init powershell --config "$env:USERPROFILE/custom_tokyo.omp.json" | Out-String) })

# Initialize Zoxide
Invoke-Expression (& { (zoxide init powershell | Out-String) })