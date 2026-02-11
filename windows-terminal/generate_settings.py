#!/usr/bin/env python3
"""Generate Windows Terminal settings from a base file and common profiles."""
import json
import sys
from pathlib import Path
import argparse


def load_json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        print(f"Failed to parse JSON from {path}: {ex}", file=sys.stderr)
        sys.exit(1)


def merge_profiles(common: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    result = {
        "defaults": {
            **common.get("defaults", {}),
            **override.get("defaults", {}),
        },
    }
    common_list = common.get("list", [])
    override_list = override.get("list", [])
    merged = []
    override_map = {p.get("guid"): p for p in override_list if p.get("guid")}

    for prof in common_list:
        guid = prof.get("guid")
        if guid and guid in override_map:
            merged.append({**prof, **override_map.pop(guid)})
        else:
            merged.append(prof)

    merged.extend(override_map.values())
    merged.extend([p for p in override_list if not p.get("guid")])
    result["list"] = merged
    return result


def merge_terminal_overrides(data: dict[str, object], overrides: dict[str, object]) -> dict[str, object]:
    profiles_override = overrides.get("profiles", {})
    profiles = data.get("profiles", {})
    defaults_override = profiles_override.get("defaults", {})
    if defaults_override:
        profile_defaults = profiles.get("defaults", {})
        profile_defaults.update(defaults_override)
        profiles["defaults"] = profile_defaults
        data["profiles"] = profiles

    if "schemes" in overrides:
        scheme_map = {scheme.get("name"): scheme for scheme in data.get("schemes", []) if scheme.get("name")}
        for scheme in overrides["schemes"]:
            name = scheme.get("name")
            if name and name in scheme_map:
                scheme_map[name].update(scheme)
            else:
                data.setdefault("schemes", []).append(scheme)
    return data


def generate(base: Path, common: Path, output: Path, terminal_overrides: Path | None = None) -> None:
    data = load_json(base)
    profiles = data.get("profiles", {})
    merged = merge_profiles(load_json(common), profiles)
    data["profiles"] = merged

    if terminal_overrides and terminal_overrides.exists():
        data = merge_terminal_overrides(data, load_json(terminal_overrides))

    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path, help="Path to base settings JSON")
    parser.add_argument("output", type=Path, help="Where to write merged settings")
    parser.add_argument("--common", type=Path, default=Path(__file__).parent / "common-profiles.json")
    parser.add_argument(
        "--terminal-overrides",
        type=Path,
        default=Path(__file__).parent / "terminal-profile-overrides.json",
        help="Optional generated profile overrides from canonical terminal settings",
    )
    args = parser.parse_args()
    generate(args.base, args.common, args.output, args.terminal_overrides)
