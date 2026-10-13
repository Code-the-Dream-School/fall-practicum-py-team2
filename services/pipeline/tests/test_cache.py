import pytest
import system.src.extract.extract


def test_cache():
    extract.cache_clear()
    calls = []

    def fake_extract(url):
        calls.append(url)
        return {"stations": [{"station_id": "1"}]}

    first = extract.cached_extract('https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json')
    second = extract.cached_extract('https://gbfs.lyft.com/gbfs/2.3/bay/gbfs.json')

    assert first == second
    assert len(calls) == 1