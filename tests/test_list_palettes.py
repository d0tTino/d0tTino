from pathlib import Path
import shutil

from scripts.thm import list_palettes


def test_list_palettes_outputs_names(tmp_path, capsys):
    repo_root = Path(__file__).resolve().parents[1]
    dest = tmp_path / "repo"
    (dest / "palettes").mkdir(parents=True)
    for p in (repo_root / "palettes").glob("*.toml"):
        shutil.copy(p, dest / "palettes" / p.name)

    list_palettes(dest)
    output = capsys.readouterr().out.strip().splitlines()
    assert "blacklight" in output
    assert "dracula" in output

