import pytest
from pipeline.extract import extract

def test_cache(monkeypatch):
    extract.cache_clear()
    calls = []

    def fake_extract(url):
        calls.append(url)
        return {"stations": [{"station_id": "1"}]}

    # LARRENZ: Used monkeypatch so cached_extract uses fake_extract instead of calling the live Lyft API
    monkeypatch.setattr(extract, "extract", fake_extract)

    url = "https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json"
    first = extract.cached_extract(url)
    second = extract.cached_extract(url)

    assert first == second
    assert len(calls) == 1