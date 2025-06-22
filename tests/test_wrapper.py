import pytest

dspy = pytest.importorskip("dspy")
from llm.universal_dspy_wrapper_v2 import LoggedFewShotWrapper

class EchoPrediction:
    def __init__(self, text: str) -> None:
        self.out = text

    def as_dict(self):
        return {"out": self.out}

class EchoModule(dspy.Module):
    def forward(self, text: str):
        return EchoPrediction(text.upper())

def test_multiple_recompilations(tmp_path):
    log_dir = tmp_path / "logs"
    fewshot_dir = tmp_path / "fewshot"
    wrapper = LoggedFewShotWrapper(
        EchoModule(),
        log_dir=log_dir,
        fewshot_dir=fewshot_dir,
    )

    # Log a single example
    wrapper(text="hello")
    wrapper.snapshot_log_to_fewshot(replace=True)
    wrapper.recompile_from_fewshot()
    first_trainset_size = len(wrapper._trainset)
    first_compiled_id = id(wrapper.compiled)

    # Recompile again; should not raise and trainset size should remain
    wrapper.recompile_from_fewshot()
    assert len(wrapper._trainset) == first_trainset_size == 1
    second_compiled_id = id(wrapper.compiled)
    assert second_compiled_id != first_compiled_id

    # A third recompile for good measure
    wrapper.recompile_from_fewshot()
    assert len(wrapper._trainset) == 1
    assert id(wrapper.compiled) != second_compiled_id
