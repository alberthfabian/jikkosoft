from __future__ import annotations
import sqlite3
import json
from typing import Any, Dict, Optional
from datetime import datetime

from ..domain.repositories import CacheRepository
from ..config import DB_PATH


class SQLiteCacheRepository(CacheRepository):
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path

    def save(
        self,
        key: str,
        value: Any,
        version: int,
        expires_at_iso: Optional[str],
    ) -> None:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO cache (key, value_json, version, expires_at) VALUES (?, ?, ?, ?)",
            (key, json.dumps(value), version, expires_at_iso),
        )
        con.commit()
        con.close()

    def delete(self, key: str) -> None:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("DELETE FROM cache WHERE key = ?", (key,))
        con.commit()
        con.close()

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT key, value_json, version, expires_at FROM cache")
        rows = cur.fetchall()
        con.close()

        result: Dict[str, Dict[str, Any]] = {}
        for key, value_json, version, expires_at in rows:
            result[key] = {
                "value": json.loads(value_json),
                "version": int(version),
                "expires_at": datetime.fromisoformat(expires_at) if expires_at else None,
            }
        return result


