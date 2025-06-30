# Load functions for interactive shell

function ai {
    param([string]$Prompt)
    python -m llm.ai_router "$Prompt"

}

