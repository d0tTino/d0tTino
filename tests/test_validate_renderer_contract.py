import json
import subprocess
from pathlib import Path


def test_validate_renderer_contract_emits_json_report(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report_file = tmp_path / "renderer-contract.json"

    subprocess.run(
        [
            "bash",
            "dotfiles/terminal/.config/tino/validate-renderer-contract.sh",
            "--report-format",
            "json",
            "--report-file",
            str(report_file),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(report_file.read_text(encoding="utf-8"))
    providers = {item["name"]: item["capabilities"] for item in report["providers"]}

    assert providers["ghostty"]["TINO_TERMINAL_EFFECTS"] == "applied"
    assert providers["wezterm"]["TINO_TERMINAL_EFFECTS"] == "unsupported"
    assert providers["windows-terminal"]["TINO_TERMINAL_OPACITY"] == "applied"


def test_validate_renderer_contract_emits_markdown_report(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report_file = tmp_path / "renderer-contract.md"

    subprocess.run(
        [
            "bash",
            "dotfiles/terminal/.config/tino/validate-renderer-contract.sh",
            "--report-format",
            "markdown",
            "--report-file",
            str(report_file),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    report = report_file.read_text(encoding="utf-8")
    assert "| Provider | FPS | Opacity | Effects |" in report
    assert "| windows-terminal | ❌ unsupported | ✅ applied | ✅ applied |" in report


def test_wezterm_fallback_matches_baseline_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fallback = (repo_root / "dotfiles/terminal/.config/wezterm/wezterm.lua").read_text(encoding="utf-8")

    assert "-- Authoritative terminal profile rendered by terminal-profile.sh." in fallback
    assert "-- Safe baseline fallback when wezterm.generated.lua is unavailable." in fallback
    assert "font_with_fallback" in fallback
    assert "window_background_opacity" in fallback
    assert "window_padding" in fallback
    assert "colors = {" in fallback
