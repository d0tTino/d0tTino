$ErrorActionPreference = 'Stop'

param(
    [string] $ImageName = $Env:IMAGE_NAME
)

if (-not $ImageName) {
    $ImageName = 'd0ttino:latest'
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'docker is required but not installed.'
    exit 1
}

$repoRoot = Join-Path $PSScriptRoot '..'
$dockerfile = Join-Path $repoRoot 'Dockerfile'
if (-not (Test-Path $dockerfile)) {
    Write-Error "Dockerfile not found in $repoRoot"
    exit 1
}

docker build -t $ImageName $repoRoot
& docker run --rm -it -v "$repoRoot":"$repoRoot" -w "$repoRoot" $ImageName @Args
