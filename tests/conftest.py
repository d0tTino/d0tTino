import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("llm") is None:
    # Ensure the repository root is on sys.path when running tests directly
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    if importlib.util.find_spec("llm") is None:
        raise ImportError(
            "The 'llm' package could not be imported. Install this repository with 'pip install -e .' before running tests."
        )
