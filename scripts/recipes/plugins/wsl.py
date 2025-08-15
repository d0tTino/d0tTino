"""WSL recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install the Windows Subsystem for Linux with required features."""
    return [
        "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart",
        "dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart",
        "wsl --install",
        "wsl --set-default-version 2",
    ]


register_recipe("wsl", run)

__all__ = ["run"]
