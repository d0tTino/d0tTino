"""Lightweight subset of the :mod:`typer` API for tests."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional

__all__ = [
    "Argument",
    "BadParameter",
    "Context",
    "Exit",
    "Option",
    "Typer",
    "echo",
]


class Exit(Exception):
    """Exception raised to emulate :class:`typer.Exit`."""

    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = code


@dataclass
class Context:
    """Minimal context object carrying arbitrary state."""

    obj: Any = None


def echo(message: Any, *, err: bool = False) -> None:
    stream = sys.stderr if err else sys.stdout
    print(message, file=stream)


def Argument(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401 - dynamic API
    return default


def Option(default: Any = None, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401 - dynamic API
    return default


class Typer:
    """No-op command registry supporting decorator syntax."""

    def __init__(
        self,
        *,
        help: Optional[str] = None,
        no_args_is_help: bool | None = None,
        hidden: bool | None = None,
    ) -> None:
        self.help = help
        self.no_args_is_help = no_args_is_help
        self.hidden = hidden

    def command(
        self,
        name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def callback(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def add_typer(self, app: "Typer", *, name: Optional[str] = None) -> None:
        return None


class BadParameter(Exception):
    """Placeholder to satisfy imports."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
