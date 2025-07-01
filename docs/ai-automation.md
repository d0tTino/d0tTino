# AI Automation

This document outlines how the repository manages tasks related to local AI workflows.

## Overview

- **Local LLM orchestration** – scripts under `llm/` control local models with minimal dependencies.
- **Task automation** – shell and PowerShell scripts handle linting, testing, and deployment.
- **Extensibility** – additional prompts and workflows can be added under `llm/prompts`.

## Installation

1. Ensure Python 3.10 or higher is installed.
2. Install the required Python packages:

   ```bash
   pip install -e . -r requirements.txt
   ```

Lint the codebase with `ruff`:

```bash
ruff check .
```


`dspy` (version 2.6.27) powers the local LLM wrapper found in `llm/`, while
`pytest` runs the test suite.

## LLM Routing CLI

Use the `ai` command to route prompts to your configured language model. By
default the tool sends the request to your remote provider, but passing
`--local` forces evaluation with the local LLM instead.

```bash
# Send the prompt to the provider configured in your environment
ai "Write a Python script"

# Run the prompt against the locally installed model
ai --local "Translate text"

# Read a prompt from standard input
echo "Summarize" | ai --stdin
```

By default the tool picks the backend automatically based on the prompt length.
Set `LLM_ROUTING_MODE` to `remote` or `local` to force the behavior, or tweak
`LLM_COMPLEXITY_THRESHOLD` to adjust when the prompt is considered complex.

## LLM Configuration

`get_preferred_models()` reads model names from a JSON file. By default the
project looks for `llm/llm_config.json` in the repository root, but you can set
`LLM_CONFIG_PATH` to specify another location or pass a path when calling the
function.

Example configuration:

```json
{
  "primary_model": "gpt-4",
  "fallback_model": "gpt-3.5-turbo"
}
```

## Shell Command Planning

`scripts/ai_exec.py` converts high level requests into shell commands using the
same backend as the `ai` helper. Each command is printed before execution and
requires an explicit `y` confirmation; pressing `Enter` or `n` skips that
command.

Examples:

```bash
# Build and install dependencies
python scripts/ai_exec.py "create a venv and install requirements"

# Commit and push changes using the local model
python scripts/ai_exec.py "git add . && git commit -m 'update' && git push" --local
```

This interactive review makes the workflow safer by ensuring you see and approve
every command before it runs.
