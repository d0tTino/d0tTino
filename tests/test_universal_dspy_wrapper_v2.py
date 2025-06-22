import dspy
import pytest  # noqa: F401
import subprocess
from pathlib import Path

from llm.universal_dspy_wrapper_v2 import LoggedFewShotWrapper, is_repo_data_path



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
    repo_root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
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

