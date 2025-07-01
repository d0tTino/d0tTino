from __future__ import annotations

from abc import ABC, abstractmethod


class Backend(ABC):
    """Lightweight interface for language model backends."""

    @abstractmethod
    def run(self, prompt: str) -> str:
        """Return the completion for ``prompt``."""
        raise NotImplementedError
