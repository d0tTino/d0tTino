from scripts import query_sources


def test_find_by_tag() -> None:
    results = query_sources.find_sources(tags=["python"])
    assert any(r["name"] == "Python Docs" for r in results)


def test_find_by_name() -> None:
    results = query_sources.find_sources(name="Rust")
    assert len(results) == 1
    assert results[0]["name"] == "Rust Book"


def test_find_by_category() -> None:
    results = query_sources.find_sources(category="DevOps")
    assert len(results) == 1
    assert results[0]["name"] == "Docker Documentation"


def test_find_by_multiple_tags() -> None:
    results = query_sources.find_sources(tags=["python", "web"])
    assert len(results) == 1
    assert results[0]["name"] == "FastAPI"


def test_find_by_category_and_tags() -> None:
    results = query_sources.find_sources(category="Framework", tags=["python"])
    assert len(results) == 1
    assert results[0]["name"] == "FastAPI"


def test_main_returns_zero_and_outputs(capsys) -> None:
    rc = query_sources.main(["--tag", "docker"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Docker Documentation" in output


def test_main_category_and_tag(capsys) -> None:
    rc = query_sources.main(["--category", "Framework", "--tag", "python"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "FastAPI" in output
