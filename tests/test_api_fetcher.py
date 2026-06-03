import unittest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.api_fetcher import _cache_get, _cache_set, CACHE_TTL_SECONDS
from datetime import datetime, timedelta


class TestCache(unittest.TestCase):
    def setUp(self):
        from backend import api_fetcher
        api_fetcher.CACHE.clear()
        api_fetcher.CACHE_TTL.clear()

    def test_cache_set_get(self):
        _cache_set("test_key", 123)
        self.assertEqual(_cache_get("test_key"), 123)

    def test_cache_expiry(self):
        _cache_set("expire_key", "value")
        from backend import api_fetcher
        api_fetcher.CACHE_TTL["expire_key"] = datetime.now() - timedelta(seconds=CACHE_TTL_SECONDS + 10)
        self.assertIsNone(_cache_get("expire_key"))

    def test_cache_miss(self):
        self.assertIsNone(_cache_get("nonexistent"))

    def test_cache_ttl_config(self):
        self.assertGreater(CACHE_TTL_SECONDS, 0)
        self.assertIsInstance(CACHE_TTL_SECONDS, int)


if __name__ == "__main__":
    unittest.main()
