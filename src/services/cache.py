import asyncio
import dataclasses
import json
import logging
import os
import platform
import time
from collections import OrderedDict

import aiosqlite

from core.constants import CACHE_MEM_MAX_SIZE, CACHE_SWEEP_INTERVAL

logger = logging.getLogger("score808.cache")


def _get_db_path() -> str:
    app_dir = os.environ.get("FLET_APP_DIR")
    if app_dir:
        return os.path.join(app_dir, "score808_cache.db")
    if platform.system() == "Android":
        return os.path.join(os.path.expanduser("~"), "score808_cache.db")
    return os.path.join("storage", "data", "score808_cache.db")


def _encode_dataclass(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class Cache:
    def __init__(self, db_path: str | None = None):
        self.db_path = os.path.abspath(db_path or _get_db_path())
        self._db: aiosqlite.Connection | None = None
        self._mem_cache: OrderedDict[str, tuple[object, float]] = OrderedDict()
        self._sweep_task: asyncio.Task | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute("PRAGMA journal_mode=WAL;")
            await self._db.execute("PRAGMA synchronous=NORMAL;")
            await self._db.execute("PRAGMA cache_size=-2000;")
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires INTEGER
                )
            """)
            await self._db.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires)")
            await self._db.commit()
            logger.info("Cache database initialized at %s", self.db_path)
        return self._db

    def _get_mem(self, key: str) -> object | None:
        if key in self._mem_cache:
            value, expiry = self._mem_cache[key]
            if time.time() < expiry:
                self._mem_cache.move_to_end(key)
                return value
            del self._mem_cache[key]
        return None

    def _set_mem(self, key: str, value: object, ttl: int = 60):
        while len(self._mem_cache) >= CACHE_MEM_MAX_SIZE:
            self._mem_cache.popitem(last=False)
        self._mem_cache[key] = (value, time.time() + ttl)
        self._mem_cache.move_to_end(key)

    async def get(self, key: str) -> str | None:
        mem = self._get_mem(key)
        if mem is not None:
            if isinstance(mem, str):
                return mem
            return json.dumps(mem, default=_encode_dataclass)
        try:
            db = await self._get_db()
            cursor = await db.execute("SELECT value, expires FROM cache WHERE key = ?", (key,))
            row = await cursor.fetchone()
            if row:
                value, expires = row
                if expires > time.time():
                    parsed = json.loads(value)
                    self._set_mem(key, parsed)
                    return value
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()
            return None
        except aiosqlite.Error as e:
            logger.error("Cache get error for key %s: %s", key, e)
            return None

    async def set(self, key: str, value: str, ttl: int = 3600):
        self._set_mem(key, value, min(ttl, 60))
        try:
            db = await self._get_db()
            expires = int(time.time()) + ttl
            await db.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
                (key, value, expires),
            )
            await db.commit()
        except aiosqlite.Error as e:
            logger.error("Cache set error for key %s: %s", key, e)

    async def set_json(self, key: str, value, ttl: int = 3600):
        encoded = json.dumps(value, default=_encode_dataclass)
        self._set_mem(key, value, min(ttl, 60))
        try:
            db = await self._get_db()
            expires = int(time.time()) + ttl
            await db.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
                (key, encoded, expires),
            )
            await db.commit()
        except aiosqlite.Error as e:
            logger.error("Cache set error for key %s: %s", key, e)

    async def get_json(self, key: str):
        mem = self._get_mem(key)
        if mem is not None:
            return mem
        try:
            db = await self._get_db()
            cursor = await db.execute("SELECT value, expires FROM cache WHERE key = ?", (key,))
            row = await cursor.fetchone()
            if row:
                value, expires = row
                if expires > time.time():
                    parsed = json.loads(value)
                    self._set_mem(key, parsed)
                    return parsed
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()
            return None
        except (aiosqlite.Error, json.JSONDecodeError) as e:
            logger.error("Cache get_json error for key %s: %s", key, e)
            return None

    async def invalidate(self, key: str):
        self._mem_cache.pop(key, None)
        try:
            db = await self._get_db()
            await db.execute("DELETE FROM cache WHERE key = ?", (key,))
            await db.commit()
        except aiosqlite.Error as e:
            logger.error("Cache invalidate error for key %s: %s", key, e)

    async def clear(self):
        self._mem_cache.clear()
        try:
            db = await self._get_db()
            await db.execute("DELETE FROM cache")
            await db.commit()
        except aiosqlite.Error as e:
            logger.error("Cache clear error: %s", e)

    async def sweep_expired(self):
        try:
            db = await self._get_db()
            cursor = await db.execute("DELETE FROM cache WHERE expires < ?", (int(time.time()),))
            await db.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info("Swept %d expired cache entries", deleted)
        except aiosqlite.Error as e:
            logger.error("Cache sweep error: %s", e)

    async def start_sweep(self, interval: int = CACHE_SWEEP_INTERVAL):
        async def _sweep_loop():
            while True:
                await asyncio.sleep(interval)
                await self.sweep_expired()

        self._sweep_task = asyncio.create_task(_sweep_loop())
        logger.info("Cache sweep started (interval=%ds)", interval)

    async def close(self):
        if self._sweep_task:
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Cache database closed")
