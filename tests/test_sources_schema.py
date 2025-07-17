from scripts import validate_sources


def test_sources_schema_valid() -> None:
    assert validate_sources.main([]) == 0
