from scripts import query_sources


def test_find_by_tag() -> None:
    results = query_sources.find_sources(tag="python")
    assert any(r["name"] == "Python Docs" for r in results)


def test_find_by_name() -> None:
    results = query_sources.find_sources(name="Rust")
    assert len(results) == 1
    assert results[0]["name"] == "Rust Book"


def test_main_returns_zero_and_outputs(capsys) -> None:
    rc = query_sources.main(["--tag", "docker"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Docker Documentation" in output
