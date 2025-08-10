"""
    Utility functions for the cache system.
"""
from __future__ import annotations
import httpx
from typing import Optional, Iterable
from ..schemas.cache_item import CacheItem

async def replicate_to_others(
    method: str,
    key: str,
    item: Optional[CacheItem],
    all_nodes: Iterable[str],
    internal_token: str,
    self_url: str,
) -> None:
    """
    Best-effort replication: sends PUT/DELETE to other nodes.
    Avoids replicating to itself using self_url.
    Args:
        method: The HTTP method to use.
        key: The key of the item to replicate.
        item: The item to replicate.
        all_nodes: The list of all nodes.
        internal_token: The internal token to use.
        self_url: The URL of this node.
    """
    headers = {"X-Internal-Token": internal_token}
    async with httpx.AsyncClient() as client:
        for node in all_nodes:
            if node == self_url:
                continue
            url = f"{node}/cache/{key}"
            try:
                if method == "PUT" and item:
                    await client.put(url, headers=headers, json=item.model_dump())
                elif method == "DELETE":
                    await client.delete(url, headers=headers)
            except Exception:
                # In the demo we ignore errors (node down, timeout, etc.)
                pass
