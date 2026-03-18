import json
import os
import subprocess
import sys
from pathlib import Path
import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_generate_settings():
    spec = importlib.util.spec_from_file_location(
        "generate_settings", Path("windows-terminal/generate_settings.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generated_settings_up_to_date(tmp_path):
    script = REPO_ROOT / 'windows-terminal' / 'generate_settings.py'
    base = REPO_ROOT / 'windows-terminal' / 'settings.base.json'
    common = REPO_ROOT / 'windows-terminal' / 'common-profiles.json'
    overrides = REPO_ROOT / 'windows-terminal' / 'terminal-profile-overrides.json'
    output = tmp_path / 'settings.json'
    subprocess.run(
        [
            sys.executable,
            str(script),
            str(base),
            str(output),
            '--common',
            str(common),
            '--terminal-overrides',
            str(overrides),
        ],
        check=True,
        cwd=tmp_path,
    )
    expected = (REPO_ROOT / 'windows-terminal' / 'settings.json').read_text(
        encoding='utf-8'
    )
    generated = output.read_text(encoding='utf-8')
    assert generated == expected, (
        "windows-terminal/settings.json is out of date; run generate_settings.py"
    )




def test_windows_terminal_generated_output_drift_check(tmp_path: Path) -> None:
    script = REPO_ROOT / "windows-terminal" / "generate_settings.py"
    generated = tmp_path / "settings.generated.json"
    subprocess.run(
        [
            sys.executable,
            str(script),
            str(REPO_ROOT / "windows-terminal" / "settings.base.json"),
            str(generated),
            '--terminal-overrides',
            str(REPO_ROOT / "windows-terminal" / "terminal-profile-overrides.json"),
        ],
        check=True,
        cwd=tmp_path,
    )

    committed = REPO_ROOT / "windows-terminal" / "settings.json"
    assert generated.read_text(encoding="utf-8") == committed.read_text(encoding="utf-8"), (
        "Canonical windows-terminal/settings.json drifted from generated output; "
        "run windows-terminal/generate_settings.py."
    )
def test_generate_settings_invalid_json(tmp_path: Path) -> None:
    script = REPO_ROOT / "windows-terminal" / "generate_settings.py"
    bad_base = tmp_path / "bad.json"
    bad_base.write_text("{ invalid json", encoding="utf-8")
    output = tmp_path / "out.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(bad_base),
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert f"Failed to parse JSON from {bad_base}" in result.stderr


def test_merge_profiles_duplicate_guid() -> None:
    module = _load_generate_settings()
    common = {
        "defaults": {"a": 1},
        "list": [
            {"guid": "{1111}", "name": "base", "color": "blue"},
            {"guid": "{1111}", "name": "base-dup"},
            {"name": "base-no-guid"},
        ],
    }
    override = {
        "defaults": {"b": 2},
        "list": [
            {"guid": "{1111}", "name": "override"},
            {"name": "override-no-guid"},
        ],
    }

    result = module.merge_profiles(common, override)

    assert result["defaults"] == {"a": 1, "b": 2}
    assert result["list"] == [
        {"guid": "{1111}", "name": "override", "color": "blue"},
        {"guid": "{1111}", "name": "base-dup"},
        {"name": "base-no-guid"},
        {"name": "override-no-guid"},
    ]


def test_merge_profiles_override_duplicates() -> None:
    module = _load_generate_settings()
    common = {
        "defaults": {},
        "list": [
            {"guid": "{2222}", "name": "base"},
        ],
    }
    override = {
        "defaults": {},
        "list": [
            {"guid": "{2222}", "name": "first"},
            {"guid": "{2222}", "name": "second"},
            {"name": "no-guid"},
        ],
    }

    result = module.merge_profiles(common, override)

    assert result["list"] == [
        {"guid": "{2222}", "name": "second"},
        {"name": "no-guid"},
    ]



def test_generate_with_temp_files(tmp_path: Path) -> None:
    module = _load_generate_settings()
    base = tmp_path / "base.json"
    common = tmp_path / "common.json"
    output = tmp_path / "out.json"
    base.write_text(
        json.dumps({"foo": 1, "profiles": {"defaults": {"a": 1}, "list": [{"guid": "{1}", "name": "base"}]}}),
        encoding="utf-8",
    )
    common.write_text(
        json.dumps({"defaults": {"b": 2}, "list": [{"guid": "{1}", "name": "override"}, {"name": "extra"}]}),
        encoding="utf-8",
    )

    module.generate(base, common, output)

    data = json.loads(output.read_text())
    assert data["foo"] == 1
    assert data["profiles"]["defaults"] == {"b": 2, "a": 1}
    assert data["profiles"]["list"] == [{"guid": "{1}", "name": "base"}, {"name": "extra"}]



def _run_windows_terminal_renderer(tmp_path: Path, env: dict[str, str]) -> dict[str, object]:
    repo = tmp_path / "repo"
    renderer_dir = repo / "dotfiles" / "terminal" / ".config" / "tino" / "renderers"
    renderer_dir.mkdir(parents=True)
    script_path = renderer_dir / "windows-terminal.sh"
    script_src = (REPO_ROOT / "dotfiles" / "terminal" / ".config" / "tino" / "renderers" / "windows-terminal.sh").read_text(encoding="utf-8")
    script_path.write_text(script_src, encoding="utf-8")

    full_env = {
        **os.environ,
        "TINO_TERMINAL_FONT_FAMILY": "CaskaydiaCove Nerd Font",
        "TINO_TERMINAL_FONT_SIZE": "13",
        "TINO_TERMINAL_OPACITY": "0.85",
        "TINO_TERMINAL_EFFECTS": "on",
        "TINO_TERMINAL_COLOR_0": "#000000",
        "TINO_TERMINAL_COLOR_1": "#111111",
        "TINO_TERMINAL_COLOR_2": "#222222",
        "TINO_TERMINAL_COLOR_3": "#333333",
        "TINO_TERMINAL_COLOR_4": "#444444",
        "TINO_TERMINAL_COLOR_5": "#555555",
        "TINO_TERMINAL_COLOR_6": "#666666",
        "TINO_TERMINAL_COLOR_7": "#777777",
        "TINO_TERMINAL_COLOR_8": "#888888",
        "TINO_TERMINAL_COLOR_9": "#999999",
        "TINO_TERMINAL_COLOR_10": "#aaaaaa",
        "TINO_TERMINAL_COLOR_11": "#bbbbbb",
        "TINO_TERMINAL_COLOR_12": "#cccccc",
        "TINO_TERMINAL_COLOR_13": "#dddddd",
        "TINO_TERMINAL_COLOR_14": "#eeeeee",
        "TINO_TERMINAL_COLOR_15": "#ffffff",
        "TINO_TERMINAL_BACKGROUND": "#000000",
        "TINO_TERMINAL_FOREGROUND": "#f2f2f2",
        "TINO_TERMINAL_CURSOR": "#fc17da",
        "TINO_TERMINAL_SELECTION": "#301050",
        **env,
    }

    subprocess.run(["bash", str(script_path), str(repo)], check=True, cwd=tmp_path, env=full_env)
    output = repo / "windows-terminal" / "terminal-profile-overrides.json"
    return json.loads(output.read_text(encoding="utf-8"))


def test_renderer_sets_use_acrylic_for_translucent_opacity(tmp_path: Path) -> None:
    rendered = _run_windows_terminal_renderer(tmp_path, {"TINO_TERMINAL_OPACITY": "0.75"})
    defaults = rendered["profiles"]["defaults"]
    assert defaults["useAcrylic"] is True
    assert defaults["acrylicOpacity"] == 0.75


def test_renderer_falls_back_when_acrylic_unsupported(tmp_path: Path) -> None:
    rendered = _run_windows_terminal_renderer(
        tmp_path,
        {
            "TINO_TERMINAL_OPACITY": "0.75",
            "TINO_WINDOWS_TERMINAL_ACRYLIC_SUPPORTED": "false",
        },
    )
    defaults = rendered["profiles"]["defaults"]
    assert defaults["useAcrylic"] is False
    assert defaults["acrylicOpacity"] == 1.0
