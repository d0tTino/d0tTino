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
        expected = f"- [{src['name']}]({src['url']})"
        # find matching line
        line_candidate = next(line for line in lines if line.startswith(expected))
        assert "*License:*" in line_candidate
        assert "*Tags:*" in line_candidate
        if 'api_type' in src:
            assert "*API:*" in line_candidate
        if 'stars' in src:
            assert "*Stars:*" in line_candidate
