import glob
import os


def has_non_comment_line(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return True
    return False


def test_dotfiles_have_non_comment_lines():
    for folder in (
        "dotfiles/desktop",
        "dotfiles/work_laptop",
        "dotfiles/fastfetch",
        "dotfiles/btm",
    ):
        for file_path in glob.glob(os.path.join(folder, "*")):
            assert os.path.isfile(file_path), f"{file_path} should exist"
            assert has_non_comment_line(
                file_path
            ), f"{file_path} has no non-comment lines"
