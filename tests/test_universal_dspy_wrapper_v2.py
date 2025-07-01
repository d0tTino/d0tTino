from pathlib import Path
import os

import pytest

dspy = pytest.importorskip("dspy")

from llm.universal_dspy_wrapper_v2 import (  # noqa: E402 - imported after importorskip
    _REPO_ROOT,
    LoggedFewShotWrapper,
    is_repo_data_path,
)
from llm.utils import get_repo_root  # noqa: E402 - imported after importorskip

class DummyModule(dspy.Module):
    def forward(self, value):
        return dspy.Prediction(value=value)


def test_wrapper_forward_return_type(tmp_path):
    module = DummyModule()
    wrapper = LoggedFewShotWrapper(
        module, log_dir=tmp_path / "logs", fewshot_dir=tmp_path / "fewshot"
    )
    result = wrapper.forward(value="test")
    baseline = module(value="test")
    assert isinstance(result, type(baseline))
    assert result == baseline


def test_is_repo_data_path_valid(tmp_path):
    repo_root = get_repo_root()
    valid = repo_root / "config.yaml"
    invalid_root = tmp_path / "config.yaml"
    invalid_ext = repo_root / "config.txt"

    assert is_repo_data_path(valid)
    assert not is_repo_data_path(invalid_root)
    assert not is_repo_data_path(invalid_ext)


def test_is_repo_data_path_windows_and_posix():
    posix_path = Path(f"{_REPO_ROOT.as_posix()}/file.json")
    windows_path = Path(str(_REPO_ROOT).replace("/", "\\") + "\\file.json")

    assert is_repo_data_path(posix_path)
    assert is_repo_data_path(windows_path)


def test_is_repo_data_path_mixed_case(monkeypatch):
    """Paths should be case-insensitive on Windows."""
    mixed = Path(f"{_REPO_ROOT.as_posix().upper()}/FiLe.JsOn")

    if os.name == "nt":
        assert is_repo_data_path(mixed)
    else:
        assert not is_repo_data_path(mixed)

        import importlib
        import sys

        monkeypatch.setattr("os.name", "nt", raising=False)
        sys.modules.pop("llm.universal_dspy_wrapper_v2", None)
        module = importlib.import_module("llm.universal_dspy_wrapper_v2")
        assert module.is_repo_data_path(mixed)


def test_repo_root_fallback(monkeypatch):
    """Ensure repo root falls back to cwd when git command fails."""

    def fake_get_repo_root():
        warnings.warn(
            "Git repo root detection failed: boom. Falling back to current working directory.",
            RuntimeWarning,
        )
        return Path.cwd()

    monkeypatch.setattr("llm.utils.get_repo_root", fake_get_repo_root)
    import importlib
    import sys
    import warnings

    with warnings.catch_warnings(record=True) as records:
        sys.modules.pop("llm.universal_dspy_wrapper_v2", None)
        module = importlib.import_module("llm.universal_dspy_wrapper_v2")

    assert module._REPO_ROOT == Path.cwd()
    assert any("falling back" in str(w.message).lower() for w in records)

