# Load functions for interactive shell

function ai {
    param([string]$Prompt)
    python -m ai_router "$Prompt"

}

