import os
import sys
import unittest

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from services.cache import Cache


class TestCache(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Use a temporary test database file
        self.db_path = "storage/data/test_cache.db"
        self.cache = Cache(db_path=self.db_path)

    async def asyncTearDown(self):
        await self.cache.close()
        # Clean up database files
        for suffix in ("", "-wal", "-shm"):
            path = self.db_path + suffix
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    async def test_db_initialization(self):
        db = await self.cache._get_db()
        self.assertIsNotNone(db)

        # Verify cache table is created
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache'")
        row = await cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "cache")

    async def test_get_set(self):
        await self.cache.set("test_key", "test_value", ttl=10)

        # Immediate read should succeed
        value = await self.cache.get("test_key")
        self.assertEqual(value, "test_value")

        # Invalidation
        await self.cache.invalidate("test_key")
        value = await self.cache.get("test_key")
        self.assertIsNone(value)

    async def test_get_set_expired(self):
        # Set with negative TTL so it is immediately expired
        await self.cache.set("expired_key", "expired_value", ttl=-5)

        value = await self.cache.get("expired_key")
        self.assertIsNone(value)

    async def test_json_serialization(self):
        data = {"list": [1, 2, 3], "nested": {"a": True, "b": "hello"}}
        await self.cache.set_json("json_key", data, ttl=10)

        restored = await self.cache.get_json("json_key")
        self.assertEqual(restored, data)

    async def test_clear(self):
        await self.cache.set("k1", "v1")
        await self.cache.set("k2", "v2")

        await self.cache.clear()

        self.assertIsNone(await self.cache.get("k1"))
        self.assertIsNone(await self.cache.get("k2"))

    async def test_sweep_expired(self):
        await self.cache.set("fresh", "value", ttl=10)
        await self.cache.set("stale", "value", ttl=-1)

        # Perform manual sweep
        await self.cache.sweep_expired()

        # Verify fresh exists and stale is cleaned from SQLite completely
        db = await self.cache._get_db()
        cursor = await db.execute("SELECT key FROM cache")
        rows = await cursor.fetchall()
        keys = [r[0] for r in rows]

        self.assertIn("fresh", keys)
        self.assertNotIn("stale", keys)


if __name__ == "__main__":
    unittest.main()
