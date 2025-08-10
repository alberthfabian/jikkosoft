"""
    Abstract repository for cache persistence.
"""
from __future__ import annotations
from typing import Any, Dict, Optional


class CacheRepository:
    """Abstract repository for cache persistence."""

    def save(
        self,
        key: str,
        value: Any,
        version: int,
        expires_at_iso: Optional[str],
    ) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns: key -> { value: Any, version: int, expires_at: datetime|None }
        """
        raise NotImplementedError


