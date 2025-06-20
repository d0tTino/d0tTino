from pathlib import Path

USER_PROFILE_PATH = Path(__file__).resolve().parents[1] / "powershell" / "user_profile.ps1"


def test_user_profile_not_empty():
    text = USER_PROFILE_PATH.read_text().strip()
    assert text, "user_profile.ps1 should not be empty"


def test_user_profile_contains_required_commands():
    lines = USER_PROFILE_PATH.read_text().splitlines()
    assert any("starship" in line.lower() for line in lines), "starship invocation missing"
    assert any("posh-git" in line.lower() for line in lines), "posh-git invocation missing"
    assert any("zoxide" in line.lower() for line in lines), "zoxide invocation missing"
