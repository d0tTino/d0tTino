"""LLM routing utilities that respect user preferences."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Any, Optional, Tuple


def _repo_root() -> Path:
    try:
        return Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:  # pragma: no cover
        warnings.warn(
            f"Git repo root detection failed: {exc}. Falling back to current working directory.",
            RuntimeWarning,
        )
        return Path.cwd()


_DEFAULT_CONFIG = _repo_root() / "llm" / "llm_config.json"

DEFAULT_MODEL = "llama3"


def _load_config(path: Path) -> dict[str, Any]:
    """Return configuration loaded from ``path`` if it exists, else empty dict."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:  # pragma: no cover - config should be valid
        warnings.warn(f"Failed to parse {path}: {exc}", RuntimeWarning)
        return {}


def get_preferred_models(
    default_primary: str,
    default_fallback: Optional[str] = None,
    *,
    config_path: Optional[Path] = None,
) -> Tuple[str, Optional[str]]:
    """Return primary and fallback model names using optional ``config_path`` or ``LLM_CONFIG_PATH`` env var."""
    env_path = os.environ.get("LLM_CONFIG_PATH")
    if config_path is not None:
        path = config_path
    elif env_path:
        path = Path(env_path)
    else:
        path = _DEFAULT_CONFIG
    cfg = _load_config(path)
    primary = cfg.get("primary_model", default_primary)
    fallback = cfg.get("fallback_model", default_fallback)
    return primary, fallback



def run_gemini(prompt: str, model: str | None = None) -> str:
    """Return Gemini response for ``prompt``."""
    cmd = ["gemini"]
    if model:
        cmd += ["--model", model]
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def run_ollama(prompt: str, model: str) -> str:
    """Return Ollama response for ``prompt`` using ``model``."""
    cmd = ["ollama", "run", model, prompt]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def send_prompt(prompt: str, *, local: bool = False, model: str = DEFAULT_MODEL) -> str:
    """Send ``prompt`` to Gemini or Ollama and return the response text."""
    if not local:
        try:
            return run_gemini(prompt, model)
        except (FileNotFoundError, subprocess.CalledProcessError):
            local = True
    if local:
        return run_ollama(prompt, model)
    raise RuntimeError("Unable to process prompt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Prompt to send to the model")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local model via Ollama instead of Gemini",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    try:
        output = send_prompt(args.prompt, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        return 1

    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


__all__ = [
    "get_preferred_models",
    "run_gemini",
    "run_ollama",
    "send_prompt",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
