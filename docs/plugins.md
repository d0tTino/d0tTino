# Writing a Backend Plug-in

Third-party packages can add new LLM backends without modifying this repository.
A plug-in must call `llm.backends.plugin_sdk.register_backend` when it is imported so the
backend becomes available to the routing utilities.

## Quick-start: Write your first Tino plug-in in 10 min

1. Copy one of the packages under `examples/plugins/*` to bootstrap your project.
   Each template contains a minimal `pyproject.toml` and plug-in module.
2. In your `pyproject.toml` expose a callable under the `llm.plugins` entry point:

   ```toml
   [project.entry-points."llm.plugins"]
   my_backend = "my_package.plugin:backend"
   ```
3. Implement `backend` and register it using `register_backend`:

   ```python
   from llm.backends.plugin_sdk import register_backend

   def backend(prompt: str) -> str:
       return "hello"  # your logic here

   register_backend("my_backend", backend)
   ```
4. Install the package with `pip install -e .` and run `ai-cli plugin backends list`
   to ensure it loads.
5. Open a pull request adding your package to
   [plugin-registry.json](../plugin-registry.json) so others can install it via
   the registry.

## Scaffolding a Plug-in

Use `scripts/plugin_scaffold.py` to bootstrap a backend or recipe package:

```bash
python -m scripts.plugin_scaffold demo
python -m scripts.plugin_scaffold demo --recipe
```

The plug-in helper exposes an equivalent command:

```bash
python -m scripts.plugins plugin new demo
```

The script creates a directory with a minimal `pyproject.toml`, an `mcp.json`
file and a plug-in module that defines a sample `run` function along with
`mcp_tool` metadata. Edit these stubs to implement your plug-in.

## Required Entry Point

Expose the plug-in module via the `llm.plugins` entry point group in your
`pyproject.toml`:

```toml
[project.entry-points."llm.plugins"]
my_backend = "my_package.plugins:backend"
```

`my_package.plugins:backend` should point to a module that calls
`register_backend` as shown below. When the library is installed, `llm`
automatically loads this entry point.

## Minimal Interface

A backend plug-in registers a callable that accepts a prompt and an optional
model name, returning the model's response as a string. The callable can be a
function or a method of a `Backend` subclass.

```python
from llm.backends.plugin_sdk import Backend, register_backend

class MyBackend(Backend):
    def run(self, prompt: str) -> str:
        # generate the completion using your model
        return "response"

def run(prompt: str, model: str | None = None) -> str:
    backend = MyBackend()
    return backend.run(prompt)

register_backend("my_backend", run)
```

See `llm/backends/plugins/sample.py` for a full example.

## Contributing new back-ends

1. Package your implementation as a normal Python distribution with a
   `pyproject.toml` file.
2. Expose the backend via the `llm.plugins` entry point:

   ```toml
   [project.entry-points."llm.plugins"]
   my_backend = "my_package.plugins:backend"
   ```

   The referenced module must call
   `llm.backends.plugin_sdk.register_backend("my_backend", run)` to register
   your callable.
3. Publish the package to PyPI or install it locally with `pip install -e .`.
4. Add your backend to
   [plugin-registry.json](../plugin-registry.json) and open a pull request so
   others can install it using `ai-cli plugin backends install`.

## Managing Plug-ins

Use the `ai-cli plugin` subcommand or the `plugins` helper to install or remove
third-party backends and recipes. The helper script mirrors the CLI commands
and can be invoked with `python -m scripts.plugins`.

```bash
# List available plug-ins
ai-cli plugin backends list

# The helper script exposes the same subcommands
python -m scripts.plugins backends list

# Install a plug-in
ai-cli plugin backends install sample
ai-cli plugin backends install anthropic
ai-cli plugin backends install mistral
ai-cli plugin backends install lmql

# Install a built-in backend with the helper script
python -m scripts.plugins backends install openrouter

# Remove a plug-in
ai-cli plugin backends remove sample

# Or remove it via the helper
python -m scripts.plugins backends remove openrouter
```

Recipe packages are managed via the `recipes` subcommand:

```bash
ai-cli plugin recipes list
ai-cli plugin recipes install echo
ai-cli plugin recipes remove echo
ai-cli plugin recipes sync
ai-cli plugin recipes publish dist/my_recipe-0.1-py3-none-any.whl --url https://example.com/simple

# The same actions are available via the helper script
python -m scripts.plugins recipes sync
python -m scripts.plugins recipes publish dist/my_recipe-0.1-py3-none-any.whl --url https://example.com/simple
```

`recipes sync` downloads and installs the recipe packages listed in the
registry into `scripts/recipes/packages` so they can be used offline. Run the
helper directly to sync packages to the default location:

```bash
python -m scripts.plugins recipes sync
```

Use `--dest` to specify a custom download directory:

```bash
python -m scripts.plugins recipes sync --dest /tmp/recipe_pkgs
```

Use `recipes publish` to upload a built recipe package to a registry. The helper
invokes `twine upload` under the hood, so make sure `twine` is installed:

```bash
python -m scripts.plugins recipes publish dist/my_recipe-0.1-py3-none-any.whl --url https://example.com/simple
```

Set `PLUGIN_REGISTRY_UPLOAD_URL` to configure the default upload target.

### Adding Your Plug-in

Plug-ins listed by the helper come from a remote registry. Submit a pull
request updating
[plugin-registry.json](../plugin-registry.json) with your plug-in name and the
pip package that provides it. Recipe packages go under the `recipes` section.
The file must conform to
[plugin-registry.schema.json](../plugin-registry.schema.json). The CLI fetches
this file from `https://raw.githubusercontent.com/d0tTino/d0tTino/main/plugin-registry.json`
and caches it in `~/.cache/d0ttino/plugin_registry.json` along with a timestamp.
The helper skips network requests when the cached data is newer than 24 hours
(configurable via the `PLUGIN_REGISTRY_TTL` environment variable). Override the
URL with `PLUGIN_REGISTRY_URL` during development to test your own registry and
pass `--update` to force a fresh download.

Example entry:

```json
{
  "my_backend": "my-package"
}
```

Placeholder packages for future backends follow the same format. Entries for
Anthropic, Mistral and LMQL will look like:

```json
{
  "anthropic": "d0ttino-anthropic-plugin",
  "mistral": "d0ttino-mistral-plugin",
  "lmql": "d0ttino-lmql-plugin"
}
```

### Migrating to MCP descriptors

Plug-ins now require an MCP descriptor under the `mcp.descriptor` key in the
registry. Existing entries with `server_url` and `capabilities` at the `mcp`
level must be updated to nest these fields under `mcp.descriptor`. For example:

```json
{
  "my_backend": {
    "package": "my-package",
    "mcp": {
      "descriptor": {
        "server_url": "https://example.com/mcp",
        "capabilities": []
      }
    }
  }
}
```

Run `python -m scripts.update_registry` after updating entries to ensure the
schema check passes.

Add recipe packages under the `recipes` key:

```json
{
  "recipes": {
    "my_recipe": "my-recipe-package"
  }
}
```

During development you can point `PLUGIN_REGISTRY_URL` at a JSON file
containing your entry. The file must pass validation against
`plugin-registry.schema.json`.

Sample plug-in packages for the built-in backends are included under
`examples/plugins`.

Install them directly with `pip` while developing:

```bash
pip install -e examples/plugins/openrouter
pip install -e examples/plugins/lobechat
pip install -e examples/plugins/mindbridge
pip install -e examples/plugins/anthropic
pip install -e examples/plugins/mistral
pip install -e examples/plugins/lmql
pip install -e examples/plugins/echo_recipe
pip install -e examples/plugins/sample_recipe
```

Alternatively set `PLUGIN_REGISTRY_URL` to the local registry file and
use the helper script to install them:

```bash
PLUGIN_REGISTRY_URL=plugin-registry.json python -m scripts.plugins backends install openrouter
```

You can also use the helper script to install them from the
registry:

```bash
python -m scripts.plugins backends install openrouter
python -m scripts.plugins backends install lobechat
python -m scripts.plugins backends install mindbridge
python -m scripts.plugins backends install anthropic
python -m scripts.plugins backends install mistral
python -m scripts.plugins backends install lmql
python -m scripts.plugins recipes install echo
```

### Registry Environment Variables

Configure how the helper script fetches and caches the plug-in registry using
the following variables:

- `PLUGIN_REGISTRY_URL` – Override the registry URL.
- `PLUGIN_REGISTRY_TTL` – Cache time-to-live in seconds (defaults to 86400).

The registry is cached at `~/.cache/d0ttino/plugin_registry.json`. Set the TTL
to `0` to always fetch a fresh copy.

## Built-in Backends

`llm` includes HTTP clients for OpenRouter, LobeChat and MindBridge. Set the
following environment variables to configure them:

### OpenRouter

- `OPENROUTER_API_KEY` – API token for the OpenRouter service.
- `OPENROUTER_BASE_URL` – Override the service URL (default
  `https://openrouter.ai/api/v1`).

### LobeChat

- `LOBECHAT_API_KEY` – API token for your LobeChat instance (optional).
- `LOBECHAT_BASE_URL` – Override the service URL (default
  `http://localhost:3210/api`).

### MindBridge

- `MINDBRIDGE_API_KEY` – API token for the MindBridge service (optional).
- `MINDBRIDGE_BASE_URL` – Override the service URL (default
  `https://api.mindbridge.ai/v1`).

# Writing a Recipe Plug-in

Automation recipes are small helpers that return shell steps for a goal.
A recipe exposes a callable that matches the following interface:

```python
from typing import List

from llm.backends.plugin_sdk import register_recipe, Recipe

class MyRecipe(Recipe):
    def run(self, goal: str) -> List[str]:
        return [f"echo {goal}"]

def run(goal: str) -> List[str]:
    return MyRecipe().run(goal)

register_recipe("my_recipe", run)
```

Expose the callable via the `d0ttino.recipes` entry point group so the
loader can discover it. The loader iterates
`importlib.metadata.entry_points(group="d0ttino.recipes")` to find recipes:

```toml
[project.entry-points."d0ttino.recipes"]
my_recipe = "my_package.recipes:run"
```

See `scripts/recipes/plugins/sample.py` for a simple example. Additional
examples for common automation tasks are provided in the same directory with
`build`, `test` and `deploy` recipes.
An installable package is available under `examples/plugins/sample_recipe`.
Publish a built wheel with `recipes publish` and sync recipes from a registry
with `recipes sync`:

```bash
python -m scripts.plugins recipes publish dist/build_recipe-0.1-py3-none-any.whl --url https://example.com/simple
python -m scripts.plugins recipes sync
```

## Cookiecutter Template

A cookiecutter project under `examples/plugin_template` generates new
backend or recipe packages. Install cookiecutter and run the template:

```bash
pip install cookiecutter
cookiecutter examples/plugin_template
```

Answer the prompts to create a minimal package that registers your plug‑in
via the appropriate entry point.

## Running a Recipe

Use the ``ai-cli recipe`` subcommand to execute a named recipe. The command
loads available recipes via ``discover_recipes()`` and runs the shell commands
it returns interactively.

```bash
ai-cli recipe sample "Show my goal"
ai-cli recipe build "Project"
```
