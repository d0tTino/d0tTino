#!/usr/bin/env python3
"""Provision a VM using Hyper-V Quick Create or WSL import."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.cli_common import send_notification


def _find_powershell() -> str:
    exe = shutil.which("pwsh") or shutil.which("powershell")
    if not exe:
        raise FileNotFoundError("PowerShell not found")
    return exe


def _run_hyperv(name: str, quick: bool, iso: str | None, cloud_init: Path | None) -> None:
    ps = _find_powershell()
    script = Path(__file__).with_name("create-hyperv-vm.ps1")
    cmd = [
        ps,
        "-NoLogo",
        "-NoProfile",
        "-Command",
        (
            f"& '{script}' -Name {name}"
            + (" -QuickCreate" if quick else "")
            + (f" -IsoUrl {iso}" if iso else "")
            + (f" -CloudInit {cloud_init}" if cloud_init else "")
        ),
    ]
    subprocess.run(cmd, check=True)


def _run_wsl(
    name: str,
    rootfs: Path,
    target: Path,
    version: int,
    cloud_init: Path | None,
) -> None:
    cmd = [
        "wsl",
        "--import",
        name,
        str(target),
        str(rootfs),
        "--version",
        str(version),
    ]
    subprocess.run(cmd, check=True)
    if cloud_init:
        subprocess.run(
            [
                "wsl",
                "-d",
                name,
                "--",
                "mkdir",
                "-p",
                "/var/lib/cloud/seed/nocloud",
            ],
            check=True,
        )
        subprocess.run(
            [
                "wsl",
                "-d",
                name,
                "--",
                "cp",
                str(cloud_init),
                "/var/lib/cloud/seed/nocloud/user-data",
            ],
            check=True,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    hyperv = sub.add_parser("hyperv", help="Provision a Hyper-V VM")
    hyperv.add_argument("--name", required=True)
    hyperv.add_argument("--quick", action="store_true", help="Use Quick Create")
    hyperv.add_argument("--iso-url")
    hyperv.add_argument("--cloud-init", type=Path)
    hyperv.add_argument("--notify", action="store_true", help="Send ntfy notification")

    wsl = sub.add_parser("wsl", help="Import a WSL distribution")
    wsl.add_argument("--name", required=True)
    wsl.add_argument("--rootfs", type=Path, required=True)
    wsl.add_argument("--target", type=Path, required=True)
    wsl.add_argument("--version", default=2, type=int)
    wsl.add_argument("--cloud-init", type=Path)
    wsl.add_argument("--notify", action="store_true", help="Send ntfy notification")

    args = parser.parse_args(argv)

    if args.mode == "hyperv":
        _run_hyperv(args.name, args.quick, args.iso_url, args.cloud_init)
        if args.notify:
            send_notification(f"Hyper-V VM {args.name} is ready")
    else:
        _run_wsl(args.name, args.rootfs, args.target, args.version, args.cloud_init)
        if args.notify:
            send_notification(f"WSL distro {args.name} is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
