"""Canonical Starship prompt specification used by generators and tests."""

from __future__ import annotations

STARSHIP_PROMPT_FORMAT = (
    "[┌─](bold purple)$directory$git_branch$git_state$git_status$python$kubernetes$aws$status$fill$time\n"
    "[└─](bold purple)$character\n"
)

REQUIRED_PROMPT_MODULES: tuple[str, ...] = (
    "directory",
    "git_branch",
    "git_state",
    "git_status",
    "python",
    "kubernetes",
    "aws",
    "status",
    "time",
)

STARSHIP_MODULES: list[tuple[str, dict[str, object]]] = [
    (
        "directory",
        {
            "style": "fg:bright_purple",
            "truncation_length": 4,
            "truncate_to_repo": False,
        },
    ),
    ("git_branch", {"symbol": " ", "style": "fg:purple"}),
    (
        "git_state",
        {
            "style": "fg:yellow",
            "format": "([$state( $progress_current/$progress_total)]($style) )",
        },
    ),
    (
        "git_status",
        {
            "style": "fg:bright_purple",
            "format": "([\\[$all_status$ahead_behind\\]]($style) )",
            "stashed": "📦",
        },
    ),
    (
        "python",
        {
            "symbol": " ",
            "format": "[$symbol($virtualenv )($version)]($style) ",
            "style": "fg:green",
        },
    ),
    (
        "kubernetes",
        {
            "symbol": "☸ ",
            "format": "[$symbol$context( \\($namespace\\))]($style) ",
            "style": "fg:cyan",
            "disabled": False,
        },
    ),
    (
        "aws",
        {
            "symbol": "󰸏 ",
            "format": "[$symbol$profile( \\($region\\))]($style) ",
            "style": "fg:yellow",
        },
    ),
    (
        "time",
        {
            "disabled": False,
            "format": "[$time]($style) ",
            "style": "fg:purple",
        },
    ),
    (
        "status",
        {
            "disabled": False,
            "format": "[$symbol$status]($style) ",
            "style": "fg:red",
        },
    ),
    ("nodejs", {"disabled": True}),
    ("rust", {"disabled": True}),
    ("golang", {"disabled": True}),
    ("package", {"disabled": True}),
]

MODULE_SETTINGS = {section: values for section, values in STARSHIP_MODULES}

REQUIRED_MODULE_KEYS: dict[str, tuple[str, ...]] = {
    section: tuple(MODULE_SETTINGS[section].keys())
    for section in REQUIRED_PROMPT_MODULES
}

REQUIRED_MODULE_VALUES: dict[str, dict[str, object]] = {
    section: dict(MODULE_SETTINGS[section])
    for section in REQUIRED_PROMPT_MODULES
}
