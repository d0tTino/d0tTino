from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def has_non_comment_line(path: Path) -> bool:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return True
    return False


def iter_package_files(package_dir: Path) -> list[Path]:
    return [path for path in package_dir.rglob("*") if path.is_file()]


def test_active_dotfile_packages_have_non_comment_lines():
    packages = (
        REPO_ROOT / "dotfiles" / "shell",
        REPO_ROOT / "dotfiles" / "nvim",
        REPO_ROOT / "dotfiles" / "tmux",
        REPO_ROOT / "dotfiles" / "terminal",
        REPO_ROOT / "dotfiles" / "fastfetch",
        REPO_ROOT / "dotfiles" / "btm",
        REPO_ROOT / "hosts" / "desktop",
        REPO_ROOT / "hosts" / "work_laptop",
    )

    for package in packages:
        assert package.is_dir(), f"{package} should exist"
        managed_files = iter_package_files(package)
        assert managed_files, f"{package} should contain managed files"

        for file_path in managed_files:
            assert has_non_comment_line(
                file_path
            ), f"{file_path} has no non-comment lines"


def test_readme_layout_paths_exist():
    readme_layout_paths = (
        REPO_ROOT / "dotfiles" / "shell",
        REPO_ROOT / "dotfiles" / "nvim",
        REPO_ROOT / "dotfiles" / "tmux",
        REPO_ROOT / "dotfiles" / "terminal",
        REPO_ROOT / "dotfiles" / "ghostty" / "ghostty.toml.tmpl",
        REPO_ROOT / "hosts" / "desktop",
        REPO_ROOT / "hosts" / "work_laptop",
    )

    for layout_path in readme_layout_paths:
        assert layout_path.exists(), f"README layout path missing: {layout_path}"


def test_tmux_conf_uses_preinstalled_tpm_only() -> None:
    tmux_conf = (REPO_ROOT / "dotfiles" / "tmux" / ".tmux.conf").read_text(encoding="utf-8")

    assert "set -g @plugin 'tmux-plugins/tpm'" in tmux_conf
    assert "run '~/.tmux/plugins/tpm/tpm'" in tmux_conf
    assert "git clone https://github.com/tmux-plugins/tpm" not in tmux_conf
    assert "if-shell \"test ! -d ~/.tmux/plugins/tpm\"" not in tmux_conf
