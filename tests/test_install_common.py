import os
import shutil
import subprocess
from pathlib import Path


def test_install_common_runs_without_ostype(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    repo.mkdir()

    scripts_dir = repo / "scripts"
    helpers_dir = scripts_dir / "helpers"
    helpers_dir.mkdir(parents=True)

    shutil.copy(repo_root / "scripts" / "install_common.sh", scripts_dir / "install_common.sh")

    log = tmp_path / "install.log"
    (scripts_dir / "setup-hooks.sh").write_text(
        f"#!/usr/bin/env bash\necho setup_hooks >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "install_fonts.sh").write_text(
        f"#!/usr/bin/env bash\necho install_fonts >> '{log}'\n", encoding="utf-8"
    )
    (helpers_dir / "sync_palettes.sh").write_text(
        f"#!/usr/bin/env bash\necho sync_palettes >> '{log}'\n", encoding="utf-8"
    )

    for f in [scripts_dir / "setup-hooks.sh", helpers_dir / "install_fonts.sh", helpers_dir / "sync_palettes.sh"]:
        f.chmod(0o755)

    env = os.environ.copy()
    env.pop("OSTYPE", None)

    subprocess.run(["/bin/bash", "scripts/install_common.sh"], cwd=repo, check=True, env=env)

    lines = log.read_text().splitlines()
    assert "setup_hooks" in lines
    assert "install_fonts" in lines
    assert "sync_palettes" in lines
