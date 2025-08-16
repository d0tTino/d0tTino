#!/usr/bin/env python3
"""Release helper to update manifests and publish.

This script derives the latest version from git tags, regenerates the
Winget and Scoop manifests with the correct download URLs and hashes and
optionally publishes them to upstream repositories.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    """Run a command and raise if it fails."""
    subprocess.run(cmd, check=True)


def latest_tag() -> str:
    """Return the most recent git tag."""
    return (
        subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True)
        .strip()
    )


def tag_version(tag: str) -> str:
    """Strip a leading 'v' from the tag for the version field."""
    return tag[1:] if tag.startswith("v") else tag


def build_archive(tag: str, version: str) -> Path:
    """Create the release archive for the given *tag* and *version*."""
    archive = REPO / f"tino-windows-{version}.zip"
    if archive.exists():
        archive.unlink()
    run([
        "git",
        "archive",
        tag,
        "--format=zip",
        "--output",
        str(archive),
    ])
    return archive


def file_sha256(path: Path) -> str:
    """Return the sha256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def update_winget(tag: str, version: str, sha: str) -> Path:
    """Update the Winget manifest with the provided values."""
    path = REPO / "winget" / "tino.yaml"
    with path.open() as fh:
        manifest = yaml.safe_load(fh)
    manifest["PackageVersion"] = version
    manifest["Installers"][0]["InstallerUrl"] = (
        f"https://github.com/d0tTino/d0tTino/releases/download/{tag}/tino-windows-{version}.zip"
    )
    manifest["Installers"][0]["Sha256"] = sha
    with path.open("w") as fh:
        yaml.safe_dump(manifest, fh, sort_keys=False)
    return path


def update_scoop(tag: str, version: str, sha: str) -> Path:
    """Update the Scoop manifest with the provided values."""
    path = REPO / "scoop" / "tino-bucket" / "tino.json"
    with path.open() as fh:
        manifest = json.load(fh)
    manifest["version"] = version
    manifest["url"] = (
        f"https://github.com/d0tTino/d0tTino/releases/download/{tag}/tino-windows-{version}.zip"
    )
    manifest["hash"] = sha
    with path.open("w") as fh:
        json.dump(manifest, fh, indent=4)
        fh.write("\n")
    return path


def publish_winget(manifest: Path, token: str) -> None:
    """Submit the manifest to the Winget upstream repository.

    Requires the `wingetcreate` tool and a GitHub PAT passed in *token*.
    """
    run(["wingetcreate", "submit", str(manifest), "-t", token])


def publish_scoop(manifest: Path, repo_url: str) -> None:
    """Commit the manifest to a Scoop bucket repository specified by *repo_url*."""
    with tempfile.TemporaryDirectory() as tmp:
        run(["git", "clone", repo_url, tmp])
        dest = Path(tmp) / "bucket" / manifest.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest, dest)
        run(["git", "-C", tmp, "add", str(dest.relative_to(tmp))])
        run(["git", "-C", tmp, "commit", "-m", f"Update {manifest.name}"])
        run(["git", "-C", tmp, "push"])


def main() -> None:
    tag = latest_tag()
    version = tag_version(tag)
    archive = build_archive(tag, version)
    sha = file_sha256(archive)

    winget_path = update_winget(tag, version, sha)
    scoop_path = update_scoop(tag, version, sha)

    token = os.environ.get("WINGET_TOKEN")
    if token:
        publish_winget(winget_path, token)
    else:
        print("WINGET_TOKEN not set; skipping Winget publish")

    repo_url = os.environ.get("SCOOP_BUCKET")
    if repo_url:
        publish_scoop(scoop_path, repo_url)
    else:
        print("SCOOP_BUCKET not set; skipping Scoop publish")


if __name__ == "__main__":
    main()
