import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_canonical_lsp_servers() -> list[str]:
    lsp_servers_file = REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lsp_servers.txt"
    return [line.strip() for line in lsp_servers_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def create_exe(path: Path, contents: str = "#!/usr/bin/env bash\n") -> None:
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)


def create_fake_nvim(path: Path, *, version: str = "0.9.1", log_path: Path | None = None) -> None:
    log_snippet = f"echo \"$@\" >> '{log_path}'\n" if log_path else ""
    create_exe(
        path,
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ ${1:-} == --version ]]; then\n"
        f"  echo 'NVIM v{version}'\n"
        "  exit 0\n"
        "fi\n"
        + log_snippet
        + "exit 0\n",
    )


def test_setup_nvim_clones_lazy_when_missing(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "setup-nvim.sh"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(
        bin_dir / "git",
        f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\nif [[ $1 == clone ]]; then\n  /bin/mkdir -p \"$5/.git\"\nfi\n",
    )

    nvim_log = tmp_path / "nvim.log"
    create_fake_nvim(bin_dir / "nvim", log_path=nvim_log)

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)})

    subprocess.run(["/bin/bash", str(script_path)], check=True, env=env)

    lazy_dir = tmp_path / ".local" / "share" / "nvim" / "lazy" / "lazy.nvim"
    assert (lazy_dir / ".git").is_dir()
    assert "clone --filter=blob:none --branch=stable" in git_log.read_text(encoding="utf-8")
    log_text = nvim_log.read_text(encoding="utf-8")
    assert "+Lazy! sync" in log_text
    expected_servers = " ".join(read_canonical_lsp_servers())
    assert f"+MasonInstall {expected_servers}" in log_text


def test_setup_nvim_skips_when_already_installed(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "setup-nvim.sh"

    lazy_dir = tmp_path / ".local" / "share" / "nvim" / "lazy" / "lazy.nvim" / ".git"
    lazy_dir.mkdir(parents=True)

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_log = tmp_path / "git.log"
    create_exe(bin_dir / "git", f"#!/usr/bin/env bash\necho \"$@\" >> '{git_log}'\n")
    create_fake_nvim(bin_dir / "nvim")

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)})

    subprocess.run(["/bin/bash", str(script_path)], check=True, env=env)

    assert not git_log.exists()


def test_setup_nvim_exits_on_unsupported_neovim_version(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "setup-nvim.sh"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    create_exe(bin_dir / "git", "#!/usr/bin/env bash\nexit 1\n")
    create_fake_nvim(bin_dir / "nvim", version="0.7.2")

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)})

    result = subprocess.run(["/bin/bash", str(script_path)], env=env, text=True, capture_output=True)

    assert result.returncode == 1
    assert "Neovim 0.8+ is required" in result.stderr


def test_lazy_config_supports_auto_bootstrap_and_offline_modes() -> None:
    lazy_config = (REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "config" / "lazy.lua").read_text(
        encoding="utf-8"
    )

    assert "TINO_NVIM_AUTO_BOOTSTRAP" in lazy_config
    assert "TINO_NVIM_OFFLINE" in lazy_config
    assert "git" in lazy_config



def test_lsp_runtime_and_setup_use_same_canonical_server_inventory() -> None:
    canonical_servers = read_canonical_lsp_servers()

    lsp_config = (
        REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "plugins" / "lsp.lua"
    ).read_text(encoding="utf-8")
    lsp_servers_module = (
        REPO_ROOT / "dotfiles" / "nvim" / ".config" / "nvim" / "lua" / "config" / "lsp_servers.lua"
    ).read_text(encoding="utf-8")
    setup_script = (REPO_ROOT / "scripts" / "setup-nvim.sh").read_text(encoding="utf-8")

    assert canonical_servers
    assert 'require("config.lsp_servers").servers' in lsp_config
    assert "lsp_servers.txt" in lsp_servers_module
    assert "lsp_servers_file" in setup_script
    assert "canonical provisioning flow" in lsp_config

