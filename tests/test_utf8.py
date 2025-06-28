import json

import pytest

dspy = pytest.importorskip("dspy")
from llm.universal_dspy_wrapper_v2 import (  # noqa: E402 - imported after importorskip
    LoggedFewShotWrapper,
)

def test_logged_fewshot_wrapper_reads_utf8(tmp_path):
    data = {"inputs": {"x": "café"}, "outputs": {"y": "naïve"}}
    fewshot_file = tmp_path / "Dummy_fewshot.jsonl"
    fewshot_file.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")

    class Dummy(dspy.Module):
        def forward(self, x):
            return x

    wrapper = LoggedFewShotWrapper(Dummy(), fewshot_dir=tmp_path, log_dir=tmp_path)
    assert wrapper._trainset[0].x == "café"
