import json
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

from scripts import validate_sources


def _write_tmp_sources(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def test_duplicate_name(tmp_path: Path, capsys) -> None:
    data = [
        {"name": "A", "url": "https://a.example", "category": "ref", "tags": ["t"], "license": "MIT"},
        {"name": "A", "url": "https://b.example", "category": "ref", "tags": ["t"], "license": "MIT"},
    ]
    src = _write_tmp_sources(tmp_path / "src.json", data)
    rc = validate_sources.main([str(src)])
    err = capsys.readouterr().err
    assert rc != 0
    assert "duplicate name" in err


def test_duplicate_url(tmp_path: Path, capsys) -> None:
    data = [
        {"name": "A", "url": "https://a.example", "category": "ref", "tags": ["t"], "license": "MIT"},
        {"name": "B", "url": "https://a.example", "category": "ref", "tags": ["t"], "license": "MIT"},
    ]
    src = _write_tmp_sources(tmp_path / "src.json", data)
    rc = validate_sources.main([str(src)])
    err = capsys.readouterr().err
    assert rc != 0
    assert "duplicate url" in err
