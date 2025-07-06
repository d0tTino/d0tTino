# Writing a Backend Plug-in

Third-party packages can add new LLM backends without modifying this repository.
A plug-in must call `llm.backends.register_backend` when it is imported so the
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
from llm.backends import register_backend, Backend

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
