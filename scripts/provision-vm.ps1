$ErrorActionPreference = 'Stop'

param(
    [Parameter(ValueFromRemainingArguments)]
    [string[]] $Args
)

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error 'python is required but not installed.'
    exit 1
}

& $python (Join-Path $PSScriptRoot 'provision_vm.py') @Args
