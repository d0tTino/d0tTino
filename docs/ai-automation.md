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

## Plug-in Registration

Third-party packages may add new backends by exposing an entry point in the
``llm.plugins`` group. A plug-in module should import
``llm.backends.register_backend`` and call it when loaded.

See the [backend plug-in guide](plugins.md) for a full template and interface
description.

Example ``pyproject.toml`` snippet:

```toml
[project.entry-points."llm.plugins"]
my_backend = "my_package.plugins:backend"
```

Install a community backend using the helper. For example:

```bash
python -m scripts.plugins backends install openrouter
```


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
When the mode is `auto` the router now sorts available backends by the
estimated cost of running the prompt and ignores models that cannot fit the
input within their context window.

Set `LLM_PRIMARY_BACKEND` to define which backend the router tries first. Use
`LLM_FALLBACK_BACKEND` to specify a secondary option. These variables override
the `DEFAULT_PRIMARY_BACKEND` and `DEFAULT_FALLBACK_BACKEND` constants in
`llm/router.py`, which default to `gemini` and `ollama` respectively.

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

The API now performs any LLM calls in a background thread. Routes such as
`/api/prompt` wrap `send_prompt()` with `asyncio.to_thread`, keeping the
event loop responsive while a model generates a response. The total
runtime is unchanged, but other requests can be served concurrently and
streaming endpoints may begin slightly later than before.

### Docker image

Build the container image and launch the API with Docker Compose:

```bash
docker-compose build api
docker-compose up api
```

The compose file uses the repository `Dockerfile` which installs
`requirements.txt` and runs `uvicorn api:app` on port 8000.

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
  "fallback_model": "gpt-3.5-turbo",
  "models": {
    "gpt-4": {"price_per_1k_tokens": 0.1, "max_tokens": 8192},
    "gpt-3.5-turbo": {"price_per_1k_tokens": 0.02, "max_tokens": 4096}
  }
}
```
Copy `examples/llm_config.json` and tweak the values as needed.
The optional `models` section defines per-model pricing and maximum context
size. When present, `send_prompt()` ranks available backends by the estimated
cost of processing the prompt and discards any model whose context window is too
small.

To use Anthropic's Claude models with the `superclaude` backend set the
model names accordingly:

```json
{
  "primary_model": "claude-3-opus",
  "fallback_model": "claude-instant"
}
```

### Customizing `llm_config.json`

Set the `LLM_CONFIG_PATH` environment variable to point at a different
configuration file. All CLI helpers such as `ai`, `ai-plan`, `ai-do` and the
`ai-cli` subcommands read this file via `get_preferred_models()` and
`send_prompt()`.

Example `llm_config.json` with custom pricing and context sizes:

```json
{
  "primary_model": "llama3",
  "fallback_model": "gpt-3.5-turbo",
  "models": {
    "llama3": {"price_per_1k_tokens": 0.0, "max_tokens": 8192},
    "gpt-3.5-turbo": {"price_per_1k_tokens": 0.02, "max_tokens": 4096}
  }
}
```

```bash
export LLM_CONFIG_PATH=/path/to/llm_config.json
ai "Summarize the document"
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
[`ntfy`](https://ntfy.sh) when the command completes.

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

The `do` subcommand always prints a dry-run of the planned commands before
execution. Review the output and re-run with `--dry-run` to preview only or
pass `--confirm` to execute steps marked with a `[risk:*]` tag. After the dry
run the CLI replays the output and asks for confirmation so you execute exactly
what you approved.

This interactive review makes the workflow safer by ensuring you see and approve
every step before it runs.

### Default flow

Running `ai-cli do` is the recommended default. The command performs five
stages:

1. **Plan** – draft shell commands for the goal.
2. **Dry-run** – write the numbered steps to `ai_do.log` and print them for
   review.
3. **Confirm** – replay the dry-run and require approval to continue.
4. **Capability prompts** – grant required scopes such as
   `filesystem.read`, `process.exec` or `network.fetch` before each step.
5. **Execute** – only steps marked without a `[risk:*]` tag run
   automatically. Commands tagged with `[risk:...]` require `--confirm`.

Example:

```bash
ai-cli do "set up the project" --dry-run
```

The dry-run writes numbered steps to `ai_do.log` for review:

```
1 mkdir -p .venv
2 [risk:network.fetch] pip install -r requirements.txt
```

Re-run with `--confirm` to execute the plan. Steps that require extra
permissions trigger capability prompts before running, for example:

```
Grant capability filesystem.write? [y/N]
Grant capability process.exec? [y/N]
```

This default flow surfaces risk tags in the dry-run log and requires explicit
approval before any privileged action executes.

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

## Telemetry

The CLI tools can emit anonymous usage events when analytics is enabled. Opt in
globally by exporting `EVENTS_ENABLED=true`:

```bash
export EVENTS_ENABLED=true
ai-cli do "Refactor the codebase"
```

To send events for a single command use `--analytics`:

```bash
ai-cli plan "Add tests" --analytics
```

Aggregated weekly totals are available via the `metrics` subcommand:

```bash
EVENTS_URL=https://example.com ai-cli metrics
```

### Local NATS Server

The event utilities in `ume/events.py` rely on a running
[NATS](https://nats.io) server. Launch one locally with Docker:

```bash
docker run --rm -p 4222:4222 nats:latest
```

Alternatively install `nats-server` via your package manager and run
`nats-server` directly. The CLI publishes to the server defined by the
`NATS_URL` environment variable (default: `nats://127.0.0.1:4222`) and uses
`NATS_SUBJECT` to choose the subject (default: `telemetry.events`). Export these
variables along with `EVENTS_ENABLED=true` to enable streaming:

```bash
export NATS_URL=nats://127.0.0.1:4222
export NATS_SUBJECT=telemetry.events
export EVENTS_ENABLED=true
```

Pass `--nats-url` to `ai-cli` to override the server per command:

```bash
ai-cli do "Refactor the codebase" --analytics --nats-url "$NATS_URL"
```




## CLI RLHF Prototype

The repository includes `cli_rlhf.py`, an experimental script for training a language model to produce shell commands. It relies on optional packages that are not installed with the default requirements:

```bash
pip install torch transformers datasets trl
```

Run the script directly to launch a short PPO training session:

```bash
python cli_rlhf.py
```

Once the dependencies above are installed, execute the script from the repository root using the same command. The prototype used to overwrite its own source file to track parameters, but it no longer modifies itself, so repeated runs leave `cli_rlhf.py` unchanged.

Training logs are written to `cli_rlhf_rewards.csv` and the final model weights are saved under the `cli_rlhf_model/` directory.
Refer to [tests/test_cli_rlhf.py](../tests/test_cli_rlhf.py) for a minimal test exercising the training loop with stubs.

## TaskCascadence Integration

[`D0tTinoTask`](https://github.com/mcandeia/taskcascadence) orchestrates the CLI helpers. It first invokes `ai-plan` to generate a plan of shell commands and then executes the approved steps with `ai`. Telemetry works the same as any other CLI command—export the analytics environment variables before running the workflow:

```bash
export EVENTS_ENABLED=true
export EVENTS_URL=https://example.com/events
export EVENTS_TOKEN=your-anon-key
```

Example TaskCascadence step:

```yaml
steps:
  - uses: d0tTino/tasks/D0tTinoTask@v1
    with:
      goal: "Update dependencies"
```

