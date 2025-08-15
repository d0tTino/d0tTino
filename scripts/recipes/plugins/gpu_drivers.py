"""GPU drivers recipe plug-in."""
from __future__ import annotations

from typing import List

from llm.backends.plugin_sdk import register_recipe


def run(_: str) -> List[str]:
    """Install NVIDIA GPU drivers and CUDA toolkit."""
    return [
        "winget install -e --id Nvidia.DisplayDriver",
        "winget install -e --id Nvidia.CUDA",
    ]


register_recipe("gpu_drivers", run)

__all__ = ["run"]
