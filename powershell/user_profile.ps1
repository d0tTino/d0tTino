# === dev-setup profile ==================================================
# Starship prompt
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression ((& starship init powershell) -join "`n")
}

# posh-git (branch + status decorations)
Import-Module posh-git -ErrorAction SilentlyContinue

# zoxide smart cd (if installed)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression ((& zoxide init powershell) -join "`n")
}
# fzf tab-completion
if (Get-Module -ListAvailable -Name PSReadLine) {
    Import-Module PSReadLine
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
}
# ========================================================================
