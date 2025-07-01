# Install Gemini CLI and pull the default Ollama model.
$ErrorActionPreference = 'Stop'

if (-not (Get-Command gemini -ErrorAction SilentlyContinue)) {
    if (Get-Command pipx -ErrorAction SilentlyContinue) {
        pipx install gemini-cli
    } elseif (Get-Command pip -ErrorAction SilentlyContinue) {
        pip install --user gemini-cli
    } else {
        Write-Error 'pip or pipx is required to install gemini-cli.'
        exit 1
    }
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error 'ollama is required but not installed.'
    exit 1
}

$defaultModel = 'llama3'
ollama pull $defaultModel
