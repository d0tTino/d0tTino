import importlib.util
import sys
import os
from pathlib import Path

if importlib.util.find_spec("llm") is None:
    # Ensure the repository root is on sys.path when running tests directly
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    if importlib.util.find_spec("llm") is None:
        raise ImportError(
            "The 'llm' package could not be imported. Install this repository with 'pip install -e .' before running tests."
        )


def pytest_configure(config):
    """Normalize cached node IDs across operating systems."""
    if os.name == "nt":
        return
    try:
        nodeids = config.cache.get("cache/nodeids", [])
    except NotImplementedError:
        config.cache.set("cache/nodeids", [])
        return

    normalized = []
    changed = False
    for nid in nodeids:
        if hasattr(nid, "as_posix"):
            normalized.append(nid.as_posix())
            changed = True
        else:
            normalized.append(str(nid))

    if changed:
        config.cache.set("cache/nodeids", normalized)
