# === dev-setup profile ==================================================
# Starship prompt
if (Get-Command starship -ErrorAction SilentlyContinue) {
    $Env:STARSHIP_CONFIG = Join-Path (Split-Path $PSScriptRoot -Parent) 'starship.toml'
    Invoke-Expression ((& starship init powershell) -join "`n")
}

# posh-git (branch + status decorations)
Import-Module posh-git -ErrorAction SilentlyContinue

# fzf tab-completion
if (Get-Module -ListAvailable -Name PSReadLine) {
    Import-Module PSReadLine
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
}
# ========================================================================
# zoxide smart cd (if installed)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression ((& zoxide init powershell) -join "`n")
}
