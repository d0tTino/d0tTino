from pathlib import Path

from scripts import generate_sources_md


def test_awesome_sources_md_up_to_date():
    sources = generate_sources_md.load_sources()
    markdown = generate_sources_md.generate_markdown(sources)
    current = Path("docs/awesome-sources.md").read_text(encoding="utf-8")
    assert markdown == current


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
