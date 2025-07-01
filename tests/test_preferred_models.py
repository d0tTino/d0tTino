import json

from llm.ai_router import get_preferred_models


def test_defaults_returned_when_config_missing(tmp_path):
    path = tmp_path / "missing.json"
    primary, fallback = get_preferred_models("p", "f", config_path=path)
    assert primary == "p"
    assert fallback == "f"


def test_reading_from_config(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"primary_model": "x", "fallback_model": "y"}))
    primary, fallback = get_preferred_models("p", "f", config_path=cfg)
    assert primary == "x"
    assert fallback == "y"


def test_env_var_overrides_default(tmp_path, monkeypatch):
    cfg = tmp_path / "env.json"
    cfg.write_text(json.dumps({"primary_model": "m1", "fallback_model": "m2"}))
    monkeypatch.setenv("LLM_CONFIG_PATH", str(cfg))
    primary, fallback = get_preferred_models("p", "f")
    assert primary == "m1"
    assert fallback == "m2"
