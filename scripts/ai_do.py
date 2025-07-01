#!/usr/bin/env python3
"""Execute shell commands with interactive confirmation."""

from __future__ import annotations

import argparse
import subprocess
from typing import Iterable


def confirm(cmd: str) -> bool:
    """Return ``True`` if the user confirms running ``cmd``."""
    resp = input(f"Run '{cmd}'? [y/N]: ")
    return resp.strip().lower().startswith("y")


def run_commands(commands: Iterable[str]) -> int:
    """Run each command after confirmation. Return the last exit code."""
    rc = 0
    for cmd in commands:
        print(cmd)
        if confirm(cmd):
            completed = subprocess.run(cmd, shell=True)
            rc = completed.returncode
            if rc != 0:
                break
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commands", nargs="+", help="Shell commands to run")
    args = parser.parse_args(argv)
    return run_commands(args.commands)


if __name__ == "__main__":
    raise SystemExit(main())
