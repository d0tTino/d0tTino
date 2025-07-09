"""Template backend plug-in."""

from __future__ import annotations

from ..plugin_sdk import Backend, register_backend


class SampleBackend(Backend):
    """Example backend that echoes the prompt."""

    def run(self, prompt: str) -> str:  # pragma: no cover - simple example
        return f"Echo: {prompt}"


def run_sample(prompt: str, model: str | None = None) -> str:
    """Return a simple echo response."""

    backend = SampleBackend()
    return backend.run(prompt)


register_backend("sample", run_sample)

__all__ = ["SampleBackend", "run_sample"]
