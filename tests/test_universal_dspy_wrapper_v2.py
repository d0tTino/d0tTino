import warnings
from pathlib import Path

import dspy
import pytest

from llm.universal_dspy_wrapper_v2 import LoggedFewShotWrapper


class DummyModule(dspy.Module):
    def forward(self, text: str):
        return text.upper()


def test_forward_write_failure(monkeypatch, tmp_path):
    wrapper = LoggedFewShotWrapper(DummyModule(), log_dir=tmp_path, fewshot_dir=tmp_path)
    original_open = Path.open

    def fake_open(self, *args, **kwargs):
        if self == wrapper._log_file:
            raise OSError("fail")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)
    with warnings.catch_warnings(record=True) as w:
        result = wrapper.forward(text="hello")
    assert result == "HELLO"
    assert any("Failed to write log data" in str(warn.message) for warn in w)

