import csv
import types
from pathlib import Path

import pytest

pytest.importorskip("torch")

import cli_rlhf


@pytest.mark.slow
def test_cli_rlhf_training_creates_rewards(tmp_path, monkeypatch):
    """train_cli_agent should write one reward entry when TRAINING_STEPS=1."""

    class DummyModel:
        pass

    monkeypatch.setattr(
        cli_rlhf.AutoModelForCausalLMWithValueHead,
        "from_pretrained",
        lambda *a, **k: DummyModel(),
    )

    class DummyTokenizer:
        eos_token = "<eos>"
        pad_token = "<pad>"

        def encode(self, text, return_tensors=None):
            return [0]

        def save_pretrained(self, path):
            Path(path).mkdir(exist_ok=True)

    monkeypatch.setattr(
        cli_rlhf.AutoTokenizer,
        "from_pretrained",
        lambda *a, **k: DummyTokenizer(),
    )

    monkeypatch.setattr(cli_rlhf.Dataset, "from_dict", lambda d: d)

    class DummyTrainer:
        def __init__(self, *, model, ref_model, tokenizer, dataset, config):
            self.model = model
            self.tokenizer = tokenizer

        def step(self, *a, **k):
            return None

        def save_model(self, path):
            Path(path).mkdir(exist_ok=True)

    monkeypatch.setattr(cli_rlhf, "PPOTrainer", DummyTrainer)

    monkeypatch.setattr(cli_rlhf.dspy, "HFModel", lambda *a, **k: object())
    monkeypatch.setattr(cli_rlhf.dspy.settings, "configure", lambda *a, **k: None)

    class DummyCtx:
        def __enter__(self):
            return None

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(cli_rlhf.dspy.settings, "context", lambda *a, **k: DummyCtx())

    class DummyPredict:
        def __call__(self, instruction):
            return types.SimpleNamespace(command="echo SUCCESS")

    monkeypatch.setattr(cli_rlhf.dspy, "Predict", lambda *a, **k: DummyPredict())

    monkeypatch.setattr(
        cli_rlhf.ShellEnvironment,
        "execute_command",
        lambda self, cmd: "SUCCESS",
    )

    monkeypatch.setattr(cli_rlhf, "TRAINING_STEPS", 1)
    csv_path = tmp_path / "cli_rlhf_rewards.csv"
    monkeypatch.setattr(cli_rlhf, "LOG_FILE_PATH", csv_path)

    cli_rlhf.train_cli_agent()

    assert csv_path.exists()
    with csv_path.open(newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2
