import pytest
from llm.universal_dspy_wrapper_v2 import LoggedFewShotWrapper

dspy = pytest.importorskip("dspy")

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


def test_snapshot_appends_and_recompiles(tmp_path):
    log_dir = tmp_path / "logs"
    fewshot_dir = tmp_path / "fewshot"
    wrapper = LoggedFewShotWrapper(
        EchoModule(),
        log_dir=log_dir,
        fewshot_dir=fewshot_dir,
    )

    # Log two examples and snapshot them
    wrapper(text="foo")
    wrapper(text="bar")
    wrapper.snapshot_log_to_fewshot(replace=True)
    initial_lines = (
        (fewshot_dir / "EchoModule_fewshot.jsonl").read_text(encoding="utf-8")
    ).splitlines()
    assert len(initial_lines) == 2
    wrapper.recompile_from_fewshot()
    first_compiled_id = id(wrapper.compiled)
    assert len(wrapper._trainset) == 2

    # Clear the log file and log two more examples
    wrapper._log_file.write_text("")
    wrapper(text="baz")
    wrapper(text="qux")
    wrapper.snapshot_log_to_fewshot()

    fewshot_lines = (
        (fewshot_dir / "EchoModule_fewshot.jsonl").read_text(encoding="utf-8")
    ).splitlines()
    assert len(fewshot_lines) == 4
    assert fewshot_lines[:2] == initial_lines

    wrapper.recompile_from_fewshot()
    assert len(wrapper._trainset) == 4
    assert id(wrapper.compiled) != first_compiled_id
