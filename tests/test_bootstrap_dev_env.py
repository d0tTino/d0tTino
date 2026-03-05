import json
import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_bootstrap_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copytree(REPO_ROOT / "scripts", repo / "scripts")
    shutil.copytree(REPO_ROOT / "dotfiles", repo / "dotfiles")
    return repo


def _create_stub(path: Path, log_file: Path) -> None:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"echo \"$(basename \"$0\"):$*\" >> '{log_file}'\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_bootstrap_dev_env_plan_mode_only_reports(tmp_path: Path) -> None:
    repo = _copy_bootstrap_repo(tmp_path)
    log_file = tmp_path / "calls.log"

    _create_stub(repo / "scripts" / "install_common.sh", log_file)
    _create_stub(repo / "scripts" / "install_dotfiles.sh", log_file)
    _create_stub(repo / "scripts" / "setup-nvim.sh", log_file)
    _create_stub(repo / "scripts" / "setup-terminal-provider.sh", log_file)
    _create_stub(repo / "dotfiles" / "terminal" / ".config" / "tino" / "validate-renderer-contract.sh", log_file)

    report_dir = tmp_path / "reports"
    env = os.environ.copy()
    env["PATH"] = f"/usr/bin:/bin:{env['PATH']}"

    subprocess.run(
        ["/bin/bash", str(repo / "scripts" / "bootstrap-dev-env.sh"), "--plan", "--report-dir", str(report_dir)],
        check=True,
        cwd=repo,
        env=env,
    )

    assert not log_file.exists()

    payload = json.loads((report_dir / "bootstrap-summary.json").read_text(encoding="utf-8"))
    assert payload["mode"] == "plan"
    assert any("dependency-install" in item for item in payload["planned_actions"])
    assert len(payload["skipped_steps"]) == 5


def test_bootstrap_dev_env_apply_runs_all_stages(tmp_path: Path) -> None:
    repo = _copy_bootstrap_repo(tmp_path)
    log_file = tmp_path / "calls.log"

    _create_stub(repo / "scripts" / "install_common.sh", log_file)
    _create_stub(repo / "scripts" / "install_dotfiles.sh", log_file)
    _create_stub(repo / "scripts" / "setup-nvim.sh", log_file)
    _create_stub(repo / "scripts" / "setup-terminal-provider.sh", log_file)
    _create_stub(repo / "dotfiles" / "terminal" / ".config" / "tino" / "validate-renderer-contract.sh", log_file)

    report_dir = tmp_path / "reports"

    subprocess.run(
        [
            "/bin/bash",
            str(repo / "scripts" / "bootstrap-dev-env.sh"),
            "--provider",
            "wezterm",
            "--host",
            "desktop",
            "--report-dir",
            str(report_dir),
        ],
        check=True,
        cwd=repo,
    )

    calls = log_file.read_text(encoding="utf-8")
    assert "install_common.sh:--dry-run --set-default-shell=skip --terminal wezterm" in calls
    assert "install_dotfiles.sh:--conflict=abort --host desktop" in calls
    assert "setup-nvim.sh:" in calls
    assert "setup-terminal-provider.sh:wezterm" in calls
    assert "validate-renderer-contract.sh:--report-format json" in calls

    payload = json.loads((report_dir / "bootstrap-summary.json").read_text(encoding="utf-8"))
    assert payload["mode"] == "apply"
    assert payload["host_overlay"] == "desktop"
    assert payload["provider_chosen"] == "wezterm"
    assert payload["skipped_steps"] == []
