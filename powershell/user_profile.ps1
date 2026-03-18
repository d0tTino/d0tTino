# === dev-setup profile ==================================================
# Starship is the only prompt/status layer.
if (Get-Command starship -ErrorAction SilentlyContinue) {
    $Env:STARSHIP_CONFIG = Join-Path (Split-Path $PSScriptRoot -Parent) 'starship.toml'
    Invoke-Expression ((& starship init powershell) -join "`n")
}

# Optional line editing enhancements that do not replace the prompt.
if (Get-Module -ListAvailable -Name PSReadLine) {
    Import-Module PSReadLine
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
}
# ========================================================================
# zoxide smart cd (if installed)
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression ((& zoxide init powershell) -join "`n")
}
