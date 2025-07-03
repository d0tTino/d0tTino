#!/usr/bin/env python3
"""Generate n8n workflow JSON using the LLM router."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from llm import router
from scripts.cli_common import read_prompt

DEFAULT_PROMPT = (
    "Create a basic n8n workflow JSON with a Start node and a Set node."
)


def generate(prompt: str) -> dict:
    """Return parsed workflow JSON for ``prompt``."""
    text = router.send_prompt(prompt)
    return json.loads(text)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="Prompt describing the workflow or '-' to read from STDIN",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write JSON to this file")
    args = parser.parse_args(argv)

    prompt = read_prompt(args.prompt)
    data = generate(prompt)
    output = json.dumps(data, indent=2)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
