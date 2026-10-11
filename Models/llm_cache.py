import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path

from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DB = PROJECT_ROOT / "data" / "llm_cache.sqlite"


class LLMCache:
    """SQLite store of structured LLM outputs, keyed by prompt hash."""

    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Workers call the LLM from parallel threads, so share one
        # connection and serialise access with a lock.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS responses "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )

    def get(self, key: str) -> str | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM responses WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO responses (key, value) VALUES (?, ?)",
                (key, value),
            )


def cache_key(model: str, schema: type[BaseModel], messages: list) -> str:
    # The schema's JSON definition is part of the key so that changing a
    # model's fields never returns a stale, incompatible response.
    payload = json.dumps(
        [model, schema.__name__, schema.model_json_schema(), messages],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def make_llm_cache() -> LLMCache | None:
    """Cache at LLM_CACHE_DB (default data/llm_cache.sqlite); "off" disables it."""
    path = os.getenv("LLM_CACHE_DB", str(DEFAULT_CACHE_DB))
    if path.strip().lower() in ("", "off", "false", "0"):
        return None
    return LLMCache(path)
