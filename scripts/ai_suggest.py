#!/usr/bin/env python3
"""Suggest up to three shell commands for a goal with risk labels and scores."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from llm import router
from llm.backends import initialize
from scripts.cli_common import build_analytics_parser, PlanStep
from scripts import cli_actions
from telemetry import analytics_default


def read_key() -> str:
    """Return a single character from stdin without waiting for ``Enter``."""
    try:  # Unix
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        try:  # Windows fallback
            import msvcrt

            return msvcrt.getch().decode()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - extremely unlikely
            return ""

initialize()

READ_COMMANDS = {"cat", "grep", "head", "ls", "more", "tail"}
WRITE_COMMANDS = {
    "chmod",
    "chown",
    "cp",
    "dd",
    "ln",
    "mkdir",
    "mv",
    "rm",
    "rmdir",
    "tee",
    "touch",
    "truncate",
    "mkfs",
}
NETWORK_COMMANDS = {
    "curl",
    "wget",
    "winget",
    "pip",
    "pip3",
    "pipx",
}

# Numeric score associated with each risk tag
RISK_SCORES = {"info": 0, "read": 1, "network": 2, "write": 3, "elevated": 4}


def _score_risk(step: str) -> tuple[List[str], int]:
    """Return risk tags for ``step`` and a numeric score."""
    try:
        tokens = shlex.split(step)
    except ValueError:
        return ["info"], RISK_SCORES["info"]
    if not tokens:
        return ["info"], RISK_SCORES["info"]
    cmd = tokens[0]
    risks: set[str] = set()
    if cmd == "sudo":
        risks.add("elevated")
        if len(tokens) > 1:
            cmd = tokens[1]
    if cmd in NETWORK_COMMANDS:
        risks.add("network")
    if cmd in WRITE_COMMANDS:
        risks.add("write")
    elif cmd in READ_COMMANDS:
        risks.add("read")
    if not risks:
        risks.add("info")
    tags = sorted(risks)
    score = max(RISK_SCORES[tag] for tag in tags)
    return tags, score


def _split_rationale(line: str) -> tuple[str, str]:
    """Split ``line`` into ``command`` and ``rationale`` parts."""
    if " # " in line:
        cmd, rationale = line.split(" # ", 1)
        return cmd.strip(), rationale.strip()
    return line.strip(), ""


def _short_help(cmd: str) -> str:
    """Return the first line of ``cmd --help`` or ``""`` on failure."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return ""
    if not tokens:
        return ""
    prog = tokens[0]
    if prog == "sudo" and len(tokens) > 1:
        prog = tokens[1]
    try:
        out = subprocess.run(
            [prog, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        line = out.stdout.splitlines()
        if line:
            return line[0].strip()
    except Exception:
        pass
    return ""


def suggest(
    goal: str,
    *,
    local: bool = False,
    model: str = router.DEFAULT_MODEL,
    context: str | None = None,
) -> List[Dict[str, object]]:
    """Return up to three suggestions with rationales and risk scores."""
    prompt = f"{goal}\nExplain each command briefly"
    text = router.shell_suggest(prompt, local=local, model=model, context=context)
    suggestions: List[Dict[str, object]] = []
    for line in text[:3]:
        cmd, rationale = _split_rationale(line)
        help_text = _short_help(cmd)
        if help_text:
            rationale = f"{rationale} ({help_text})" if rationale else help_text
        tags, score = _score_risk(cmd)
        suggestions.append(
            {"command": cmd, "rationale": rationale, "risk": {"tags": tags, "score": score}}
        )
    return suggestions


def main(argv: Optional[List[str]] = None) -> int:
    analytics = build_analytics_parser()
    parser = argparse.ArgumentParser(description=__doc__, parents=[analytics])
    parser.add_argument("goal", help="High level description of the task")
    parser.add_argument("--local", action="store_true", help="Force use of fallback backend")
    parser.add_argument(
        "--model",
        default=router.DEFAULT_MODEL,
        help="Model name for Ollama (default: %(default)s)",
    )
    parser.add_argument("--json", action="store_true", help="Output suggestions as JSON")
    args = parser.parse_args(argv)
    args.analytics = getattr(args, "analytics", analytics_default())
    try:
        suggestions = suggest(args.goal, local=args.local, model=args.model)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(exc, file=sys.stderr)
        cli_actions.record_event_logged(
            "ai-suggest", {"exit_code": 1}, enabled=args.analytics
        )
        return 1
    if args.json:
        print(json.dumps(suggestions))
    else:
        log_path = Path.home() / ".config" / "d0tTino" / "ai_suggest.log"
        for idx, item in enumerate(suggestions, 1):
            tags = ",".join(item["risk"]["tags"])
            score = item["risk"]["score"]
            print(f"{idx}. {item['command']} [risk:{tags}] (score:{score})")
            if item["rationale"]:
                print(item["rationale"])
        print(
            f"Press [1-{len(suggestions)}] to run a command or any other key to skip: ",
            end="",
            flush=True,
        )
        choice = read_key()
        print()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(suggestions):
                item = suggestions[idx - 1]
                cmd = f"{item['command']} [risk:{','.join(item['risk']['tags'])}]"
                cli_actions.run_steps(
                    "ai-suggest-run",
                    [PlanStep(1, cmd)],
                    log_path=log_path,
                    analytics=args.analytics,
                    assume_yes=True,
                    confirm=True,
                    payload={"suggestion_index": idx, "goal": args.goal},
                )
    cli_actions.record_event_logged(
        "ai-suggest",
        {"exit_code": 0, "suggestion_count": len(suggestions)},
        enabled=args.analytics,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
