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


def test_zoxide_after_fzf_block():
    """Ensure zoxide initialization occurs after the fzf setup."""
    lines = USER_PROFILE_PATH.read_text().splitlines()
    fzf_index = None
    zoxide_index = None
    for idx, line in enumerate(lines):
        if "Set-PSReadLineKeyHandler" in line:
            fzf_index = idx
        if "zoxide init powershell" in line:
            zoxide_index = idx
    assert fzf_index is not None, "fzf block not found"
    assert zoxide_index is not None, "zoxide init not found"
    assert zoxide_index > fzf_index, "zoxide initialization should follow fzf block"


def test_profile_handles_missing_tools_gracefully():
    """Starship, posh-git and zoxide should be optional."""
    lines = [line.lower() for line in USER_PROFILE_PATH.read_text().splitlines()]

    starship_line = next((line for line in lines if "get-command starship" in line), "")
    assert "if (get-command starship" in starship_line
    assert "-erroraction silentlycontinue" in starship_line

    posh_git_line = next((line for line in lines if "import-module posh-git" in line), "")
    assert "-erroraction silentlycontinue" in posh_git_line

    zoxide_line = next((line for line in lines if "get-command zoxide" in line), "")
    assert "if (get-command zoxide" in zoxide_line
    assert "-erroraction silentlycontinue" in zoxide_line
