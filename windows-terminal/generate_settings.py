#!/usr/bin/env python3
"""Generate Windows Terminal settings from a base file and common profiles."""
import json
import sys
from pathlib import Path
import argparse


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        print(f"Failed to parse JSON from {path}: {ex}", file=sys.stderr)
        sys.exit(1)


def merge_profiles(common: dict, override: dict) -> dict:
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
    # Append any profiles without guid
    merged.extend([p for p in override_list if not p.get("guid")])
    result["list"] = merged
    return result


def generate(base: Path, common: Path, output: Path) -> None:
    data = load_json(base)
    profiles = data.get("profiles", {})
    merged = merge_profiles(load_json(common), profiles)
    data["profiles"] = merged
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path, help="Path to base settings JSON")
    parser.add_argument("output", type=Path, help="Where to write merged settings")
    parser.add_argument("--common", type=Path, default=Path(__file__).parent / "common-profiles.json")
    args = parser.parse_args()
    generate(args.base, args.common, args.output)
