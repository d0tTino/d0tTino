import types
import contextlib

from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("trl")

import cli_rlhf  # noqa: E402 - imported after importorskip


def test_cli_rlhf_train_creates_log(monkeypatch, tmp_path):
    """Training should create a rewards CSV."""

    class DummyHFModel:
        def __init__(self, model=None, tokenizer=None):
            self.model = model
            self.tokenizer = tokenizer

    @contextlib.contextmanager
    def dummy_context(**_):
        yield

    class DummySettings:
        def configure(self, *, lm=None):
            self.lm = lm

        context = staticmethod(dummy_context)

    class DummyPolicy:
        def __call__(self, instruction):
            return types.SimpleNamespace(command="echo SUCCESS")

    dummy_tokenizer = types.SimpleNamespace(
        pad_token="</s>",
        eos_token="</s>",
        encode=lambda text, return_tensors=None: torch.tensor([0]),
        save_pretrained=lambda path: Path(path).mkdir(exist_ok=True),
    )

    class DummyTrainer:
        def __init__(self, *a, **k):
            self.model = "model"
            self.tokenizer = dummy_tokenizer

        def step(self, *a, **k):
            pass

        def save_model(self, directory):
            Path(directory).mkdir(exist_ok=True)

    monkeypatch.setattr(cli_rlhf, "PPOTrainer", DummyTrainer)
    monkeypatch.setattr(
        cli_rlhf, "AutoModelForCausalLMWithValueHead", types.SimpleNamespace(from_pretrained=lambda *a, **k: "model")
    )
    monkeypatch.setattr(cli_rlhf, "AutoTokenizer", types.SimpleNamespace(from_pretrained=lambda *a, **k: dummy_tokenizer))
    monkeypatch.setattr(cli_rlhf, "Dataset", types.SimpleNamespace(from_dict=lambda d: d))

    monkeypatch.setattr(cli_rlhf, "ShellEnvironment", lambda *a, **k: types.SimpleNamespace(execute_command=lambda c: "SUCCESS", get_reward=lambda s: torch.tensor(1.0)))

    monkeypatch.setattr(cli_rlhf.dspy, "HFModel", DummyHFModel)
    monkeypatch.setattr(cli_rlhf.dspy, "Predict", lambda *a, **k: DummyPolicy())
    monkeypatch.setattr(cli_rlhf.dspy, "settings", DummySettings())

    monkeypatch.setattr(cli_rlhf, "TRAINING_STEPS", 1)
    log_path = tmp_path / "rewards.csv"
    monkeypatch.setattr(cli_rlhf, "LOG_FILE_PATH", log_path)

    cli_rlhf.train_cli_agent()

    assert log_path.exists()

