import pytest

pytest.importorskip("requests")

from scripts.enrich_sources import enrich_sources


def test_enrich_sources_adds_fields(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        @staticmethod
        def json():
            return {"stargazers_count": 42}

    def fake_get(url, *, timeout):
        assert url == "https://api.github.com/repos/owner/api"
        assert timeout == 5
        return FakeResponse()

    monkeypatch.setattr("requests.get", fake_get)

    sources = [
        {"url": "https://github.com/owner/api"},
        {"url": "https://example.com/graphql"},
    ]
    enrich_sources(sources)

    assert sources[0]["api_type"] == "REST"
    assert sources[0]["stars"] == 42
    assert sources[1]["api_type"] == "GraphQL"
    assert "stars" not in sources[1]
