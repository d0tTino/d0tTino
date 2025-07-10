# Writing a Backend Plug-in

Third-party packages can add new LLM backends without modifying this repository.
A plug-in must call `llm.backends.plugin_sdk.register_backend` when it is imported so the
backend becomes available to the routing utilities.

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

## Managing Plug-ins

Use the `plugins` helper to install or remove third-party backends and recipes.

```bash
# List available plug-ins
python -m scripts.plugins list

# Install a plug-in
python -m scripts.plugins install sample

# Remove a plug-in
python -m scripts.plugins remove sample
```

Recipe packages are managed via the `recipes` subcommand:

```bash
python -m scripts.plugins recipes list
python -m scripts.plugins recipes install echo
python -m scripts.plugins recipes remove echo
```

### Adding Your Plug-in

Plug-ins listed by the helper come from a small registry file. Update
`plugin-registry.json` in this repository with your plug-in name and the pip
package that provides it. Recipe packages go under the `recipes` section.
The file must conform to
[plugin-registry.schema.json](../plugin-registry.schema.json).

Example entry:

```json
{
  "my_backend": "my-package"
}
```

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
`examples/plugins`. Install them with:

```bash
python -m scripts.plugins install openrouter
python -m scripts.plugins install lobechat
python -m scripts.plugins install mindbridge
python -m scripts.plugins recipes install echo
```

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
loader can discover it:

```toml
[project.entry-points."d0ttino.recipes"]
my_recipe = "my_package.recipes:run"
```

See `scripts/recipes/plugins/sample.py` for a simple example.

## Running a Recipe

Use the ``ai-cli recipe`` subcommand to execute a named recipe. The command
loads available recipes via ``discover_recipes()`` and runs the shell commands
it returns interactively.

```bash
ai-cli recipe sample "Show my goal"
```
