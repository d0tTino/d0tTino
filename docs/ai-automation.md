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
echo "Summarize" | ai -
```

By default the tool picks the backend automatically based on the prompt length.
Set `LLM_ROUTING_MODE` to `remote` or `local` to force the behavior, or tweak
`LLM_COMPLEXITY_THRESHOLD` to adjust when the prompt is considered complex.

## FastAPI/Next.js Dashboard

The project ships with a small FastAPI backend that exposes routes for sending
prompts, applying palettes and monitoring the Universal Memory Engine. A
Next.js front end consumes these endpoints and can also be packaged as a Tauri
desktop app.

To launch the API locally run:

```bash
uvicorn llm.api:app --reload --port 8000
```

The React dashboard connects to the same host, typically started with
`pnpm dev` on <http://localhost:3000>. The Tauri build uses the same
React code so both environments share a consistent interface.

### Legacy Streamlit interface

Earlier versions provided a Streamlit UI located at `ui/web_app.py`. It remains
for reference and can be launched with:


```bash
uvicorn api:app --reload
cd dashboard && npm install && npm run dev
```

This prototype is no longer actively developed but still mirrors the prompt
routing and palette controls.


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

To use Anthropic's Claude models with the `superclaude` backend set the
model names accordingly:

```json
{
  "primary_model": "claude-3-opus",
  "fallback_model": "claude-instant"
}
```

## Shell Command Planning

`scripts/ai_exec.py` converts a high level goal into individual shell commands
without executing them. The `ai-plan` entry point simply prints the generated
steps so you can review the plan:

```bash
ai-plan "create a venv and install requirements"
```

To run those commands interactively use `ai-do`. Each command is numbered and
requires a `y` confirmation; pressing `Enter` or `n` skips that command. Output
is appended to `ai_do.log` by default.

Both `ai-plan` and `ai-do` accept a `--notify` flag to send a notification via
[`ntfy`](https://ntfy.sh). When a topic is provided all step results are
published under `TOPIC/step-N`:

```text
https://ntfy.sh/TOPIC/step-1  # "success", "failed" or "skipped"
```

If the flag is used without an explicit value the default topic is `ai-do`.
The final completion status posts to `TOPIC` itself.

```bash
ai-do "git add . && git commit -m 'update' && git push" --log my.log
```

`ai-do` returns the exit status of the first failing command so it can be used
in scripts.

The `ai-cli` tool provides the same functionality via subcommands:

```bash
ai-cli plan "create a venv and install requirements"
ai-cli do "git add . && git commit -m 'update' && git push" --log my.log
```
Legacy commands `ai-plan` and `ai-do` now delegate to these subcommands.

This interactive review makes the workflow safer by ensuring you see and approve
every step before it runs.

## Few-Shot Logging with DSPy

DSPy's `LoggedFewShotWrapper` lets you record a module's inputs and outputs and
then compile from those examples. Because `dspy` is optional, install it
separately when you need this feature:

```bash
pip install dspy-ai
```

### Example module

```python
import dspy
from llm import LoggedFewShotWrapper


class Echo(dspy.Module):
    def forward(self, text: str) -> dspy.Prediction:
        return dspy.Prediction(out=text)


# Save logs under logs/ and few-shot data under fewshot/
mod = LoggedFewShotWrapper(Echo(), log_dir="logs", fewshot_dir="fewshot")
print(mod(text="hello").out)
```

### Snapshot and recompile

Each call to `mod` appends a JSON line to `logs/Echo_io.jsonl`. Move the logged
lines into the few-shot file and recompile:

```python
mod.snapshot_log_to_fewshot(replace=True)
mod.recompile_from_fewshot()
```

The wrapper automatically uses the compiled module on the next call. Whenever
you log new examples, run `snapshot_log_to_fewshot()` and recompile again to
extend the training set.

## n8n Integration

An example workflow for the [n8n](https://n8n.io/) automation platform lives in `n8n/flows/`. Start the service with Docker Compose:

```bash
docker-compose up -d
```

Open <http://localhost:5678> in your browser and choose **Import from File** to load `n8n/flows/mcp-ai_exec.json`. Install the `n8n-nodes-mcp` community package (use the **Manage Nodes** menu or run `npm install n8n-nodes-mcp`) and the imported workflow will include an **MCP Client** node that launches `scripts/ai_exec.py`.

## LangGraph Retrieval Example

`scripts/rag_example.py` demonstrates how to build a simple retrieval graph. First ingest a document into ChromaDB:

```bash
python scripts/etl.py examples/rag_example.txt --persist examples/chroma --collection demo
```

Then query the collection using the retrieval graph:

```bash
python scripts/rag_example.py "small document" --persist examples/chroma --collection demo
```


