import json
from pathlib import Path

from llm.ai_router import get_preferred_models


def test_get_preferred_models(tmp_path: Path) -> None:
    config = tmp_path / "llm_config.json"
    config.write_text(json.dumps({"primary_model": "foo", "fallback_model": "bar"}))
    primary, fallback = get_preferred_models("default", "alt", config_path=config)
    assert primary == "foo"
    assert fallback == "bar"


def test_get_preferred_models_defaults(tmp_path: Path) -> None:
    config = tmp_path / "missing.json"
    primary, fallback = get_preferred_models("default", "alt", config_path=config)
    assert primary == "default"
    assert fallback == "alt"


def test_get_preferred_models_env_override(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "env.json"
    config.write_text(json.dumps({"primary_model": "env"}))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(config))
    primary, fallback = get_preferred_models("default", "alt")
    assert primary == "env"
    assert fallback == "alt"

