from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime, timedelta
from typing import Dict

from .schemas.cache_item import CacheItem
from .config import NODE_ID, NODES, INTERNAL_TOKEN, is_internal_call, self_internal_url
from .persistence import init_db, load_all, save_to_db, delete_from_db
from .utils.replication import replicate_to_others

# ===== Local memory =====
# key -> { "value": Any, "version": int, "expires_at": datetime|None }
cache: Dict[str, Dict] = {}

app = FastAPI(title="Distributed Cache")

@app.on_event("startup")
def on_startup():
    """
    Initialize the database and load the cache to memory.
    """
    init_db()
    # load to memory
    global cache
    cache = load_all()
    # clean expired items at startup
    now = datetime.utcnow()
    for k, v in list(cache.items()):
        if v["expires_at"] and now > v["expires_at"]:
            delete_from_db(k)
            del cache[k]

@app.put("/cache/{key}")
async def put_item(key: str, item: CacheItem, request: Request):
    """
    Put an item in the cache.
    Args:
        key: The key of the item to put.
        item: The item to put.
        request: The request object.
    Returns:
        The status of the operation.
    """
    internal = is_internal_call(request.headers.get("X-Internal-Token"))

    expires_at = None
    if item.ttl_ms:
        expires_at = datetime.utcnow() + timedelta(milliseconds=item.ttl_ms)

    # version control (LWW by increasing integer)
    if key in cache and item.version <= cache[key]["version"]:
        raise HTTPException(status_code=409, detail="Version conflict")

    # write-through: memory + SQLite
    cache[key] = {"value": item.value, "version": item.version, "expires_at": expires_at}
    save_to_db(key, item.value, item.version, expires_at.isoformat() if expires_at else None)

    # replication to other nodes (only if coming from an external client)
    if not internal:
        await replicate_to_others(
            method="PUT",
            key=key,
            item=item,
            all_nodes=NODES,
            internal_token=INTERNAL_TOKEN,
            self_url=self_internal_url(),
        )

    return {"status": "stored", "node": NODE_ID}

@app.get("/cache/{key}")
def get_item(key: str):
    """
    Get an item from the cache.
    Args:
        key: The key of the item to get.
    Returns:
        The item.
    """
    if key not in cache:
        raise HTTPException(status_code=404, detail="Not found")

    entry = cache[key]
    if entry["expires_at"] and datetime.utcnow() > entry["expires_at"]:
        # expired → delete and report 404
        delete_from_db(key)
        del cache[key]
        raise HTTPException(status_code=404, detail="Expired")

    return {
        "value": entry["value"],
        "version": entry["version"],
        "expires_at": entry["expires_at"].isoformat() if entry["expires_at"] else None,
    }

@app.delete("/cache/{key}")
async def delete_item(key: str, request: Request):
    """
    Delete an item from the cache.
    Args:
        key: The key of the item to delete.
        request: The request object.
    Returns:
        The status of the operation.
    """
    internal = is_internal_call(request.headers.get("X-Internal-Token"))

    if key in cache:
        del cache[key]
    delete_from_db(key)

    if not internal:
        await replicate_to_others(
            method="DELETE",
            key=key,
            item=None,
            all_nodes=NODES,
            internal_token=INTERNAL_TOKEN,
            self_url=self_internal_url(),
        )

    return {"status": "deleted", "node": NODE_ID}

@app.get("/_health")
def health():
    """
    Check the health of the node.
    Returns:
        The status of the node.
    """
    return {"node": NODE_ID, "status": "ok"}
