import pathlib


def test_readme_has_config_header():
    """README should mention the configuration header."""
    readme_path = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    assert "# d0tTino Configuration" in text
