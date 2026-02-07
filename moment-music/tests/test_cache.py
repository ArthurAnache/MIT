import time

from trends.cache import TTLCache


def test_ttl_cache_fresh_and_stale(tmp_path):
    cache = TTLCache(ttl_seconds=1, persist_path=tmp_path / "cache.json")
    cache.set("FR", {"x": 1})

    v, fresh = cache.get("FR")
    assert v == {"x": 1}
    assert fresh is True

    time.sleep(1.1)
    v2, fresh2 = cache.get("FR")
    assert v2 == {"x": 1}
    assert fresh2 is False
