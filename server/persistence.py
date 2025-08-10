from __future__ import annotations
import sqlite3
from datetime import datetime
import json
from typing import Dict, Any, Optional

from .config import DB_PATH

DDL = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value_json TEXT,
    version INTEGER,
    expires_at TEXT
)
"""

def init_db(db_path: str = DB_PATH) -> None:
    """
    Initialize the database.
    Args:
        db_path: The path to the database.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(DDL)
    con.commit()
    con.close()

def save_to_db(
    key: str,
    value: Any,
    version: int,
    expires_at_iso: Optional[str],
    db_path: str = DB_PATH,
) -> None:
    """
    Save an item to the database.
    Args:
        key: The key of the item to save.
        value: The value of the item to save.
        version: The version of the item to save.
        expires_at_iso: The expiration date of the item to save.
        db_path: The path to the database.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO cache (key, value_json, version, expires_at) VALUES (?, ?, ?, ?)",
        (key, json.dumps(value), version, expires_at_iso),
    )
    con.commit()
    con.close()

def delete_from_db(key: str, db_path: str = DB_PATH) -> None:
    """
    Delete an item from the database.
    Args:
        key: The key of the item to delete.
        db_path: The path to the database.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("DELETE FROM cache WHERE key = ?", (key,))
    con.commit()
    con.close()

def load_all(db_path: str = DB_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict in memory:
    key -> { value, version, expires_at(datetime|None) }
    (The caller decides to delete expired items if desired)
    Args:
        db_path: The path to the database.
    Returns:
        A dict in memory:
        key -> { value, version, expires_at(datetime|None) }
        (The caller decides to delete expired items if desired)
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT key, value_json, version, expires_at FROM cache")
    rows = cur.fetchall()
    con.close()

    result = {}
    for key, value_json, version, expires_at in rows:
        result[key] = {
            "value": json.loads(value_json),
            "version": int(version),
            "expires_at": datetime.fromisoformat(expires_at) if expires_at else None,
        }
    return result

# Ensure DB and table exist even if FastAPI startup events are not triggered (e.g., some tests)
init_db()