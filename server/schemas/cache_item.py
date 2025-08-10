from pydantic import BaseModel
from typing import Any, Optional

class CacheItem(BaseModel):
    """
    Model of data for a cache item.
    value: The value stored.
    ttl_ms: Time to live in milliseconds.
    version: Version of the item.
    """
    value: Any
    ttl_ms: Optional[int] = None
    version: int
