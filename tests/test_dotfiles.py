import glob
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def has_non_comment_line(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return True
    return False


def test_dotfiles_have_non_comment_lines():
    for folder in (
        REPO_ROOT / "dotfiles" / "desktop",
        REPO_ROOT / "dotfiles" / "work_laptop",
        REPO_ROOT / "dotfiles" / "fastfetch",
        REPO_ROOT / "dotfiles" / "btm",
    ):
        for file_path in glob.glob(os.path.join(str(folder), "*")):
            assert os.path.isfile(file_path), f"{file_path} should exist"
            assert has_non_comment_line(
                file_path
            ), f"{file_path} has no non-comment lines"
