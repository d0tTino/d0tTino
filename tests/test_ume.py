from pathlib import Path
import json
import ume

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_sources() -> None:
    expected = json.loads((REPO_ROOT / "metadata" / "sources.json").read_text(encoding="utf-8"))
    assert ume.load_sources() == expected
