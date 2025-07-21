from pathlib import Path

import pytest

from scripts import generate_sources_md

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_awesome_sources_md_up_to_date():
    sources = generate_sources_md.load_sources()
    markdown = generate_sources_md.generate_markdown(sources)
    current = (REPO_ROOT / "docs" / "awesome-sources.md").read_text(encoding="utf-8")
    assert markdown == current, (
        "docs/awesome-sources.md is outdated. "
        "Run 'python scripts/generate_sources_md.py' and commit the result."
    )


def test_generate_markdown_details_format():
    sources = generate_sources_md.load_sources()
    markdown = generate_sources_md.generate_markdown(sources)
    lines = markdown.splitlines()
    for src in sources:
        tags = ", ".join(src.get("tags", []))
        details = f"*License:* {src.get('license', 'Unknown')} — *Tags:* {tags}"
        if "api_type" in src:
            details += f" — *API:* {src['api_type']}"
        if "stars" in src:
            details += f" — *Stars:* {src['stars']}"

        expected_line = f"- [{src['name']}]({src['url']}) — {details}"
        assert expected_line in lines


def test_generate_markdown_categories_sorted() -> None:
    sources = generate_sources_md.load_sources()
    markdown = generate_sources_md.generate_markdown(sources)
    categories = [line[3:] for line in markdown.splitlines() if line.startswith("## ")]
    assert categories == sorted(categories)


def test_failure_message_on_sources_change(tmp_path: Path) -> None:
    sources = generate_sources_md.load_sources()
    sources.append(
        {
            "name": "Tmp",
            "url": "https://example.com",
            "category": "Zzz",
            "tags": [],
            "license": "MIT",
        }
    )
    markdown = generate_sources_md.generate_markdown(sources)
    current = (REPO_ROOT / "docs" / "awesome-sources.md").read_text(encoding="utf-8")
    with pytest.raises(AssertionError) as exc:
        assert markdown == current, (
            "docs/awesome-sources.md is outdated. "
            "Run 'python scripts/generate_sources_md.py' and commit the result."
        )
    assert "Run 'python scripts/generate_sources_md.py'" in str(exc.value)
