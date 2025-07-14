from pathlib import Path

from scripts import generate_sources_md


def test_awesome_sources_md_up_to_date():
    sources = generate_sources_md.load_sources()
    markdown = generate_sources_md.generate_markdown(sources)
    current = Path("docs/awesome-sources.md").read_text(encoding="utf-8")
    assert markdown == current
