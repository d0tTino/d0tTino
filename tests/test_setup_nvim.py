import os
import subprocess
from pathlib import Path


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def test_setup_nvim_clones_lazy_when_missing(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "setup-nvim.sh"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(
        bin_dir / "git",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$5/.git\"\nfi\n",
    )

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)})

    subprocess.run(["/bin/bash", str(script_path)], check=True, env=env)

    lazy_dir = tmp_path / ".local" / "share" / "nvim" / "lazy" / "lazy.nvim"
    assert (lazy_dir / ".git").is_dir()
    assert "clone --filter=blob:none --branch=stable" in git_log.read_text(encoding="utf-8")


def test_setup_nvim_skips_when_already_installed(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "setup-nvim.sh"

    lazy_dir = tmp_path / ".local" / "share" / "nvim" / "lazy" / "lazy.nvim" / ".git"
    lazy_dir.mkdir(parents=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(bin_dir / "git", f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\n")

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)})

    subprocess.run(["/bin/bash", str(script_path)], check=True, env=env)

    assert not git_log.exists()
