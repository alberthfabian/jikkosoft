"""
    Service for the cache system.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from ..domain.repositories import CacheRepository
from ..domain.conflict_resolution import ConflictResolutionStrategy


class CacheService:
    def __init__(
        self,
        repository: CacheRepository,
        conflict_strategy: ConflictResolutionStrategy,
        replicate_supplier,
    ) -> None:
        self._repository = repository
        self._conflict = conflict_strategy
        self._replicate_supplier = replicate_supplier
        self._cache: Dict[str, Dict[str, Any]] = {}

    # ----- lifecycle -----
    def load_from_repository(self) -> None:
        self._cache = self._repository.load_all()
        now = datetime.utcnow()
        for k, v in list(self._cache.items()):
            if v["expires_at"] and now > v["expires_at"]:
                self._repository.delete(k)
                del self._cache[k]

    # ----- operations -----
    def get(self, key: str) -> Dict[str, Any]:
        if key not in self._cache:
            raise KeyError("Not found")
        entry = self._cache[key]
        if entry["expires_at"] and datetime.utcnow() > entry["expires_at"]:
            self._repository.delete(key)
            del self._cache[key]
            raise KeyError("Expired")
        return entry

    async def put(
        self,
        *,
        key: str,
        value: Any,
        version: int,
        ttl_ms: Optional[int],
        internal: bool,
        nodes,
        internal_token: str,
        self_url: str,
        item_model,
    ) -> None:
        expires_at: Optional[datetime] = None
        if ttl_ms:
            expires_at = datetime.utcnow() + timedelta(milliseconds=ttl_ms)

        if key in self._cache:
            if self._conflict.is_conflict(version, self._cache[key]["version"]):
                raise ValueError("conflict")

        self._cache[key] = {"value": value, "version": version, "expires_at": expires_at}
        self._repository.save(key, value, version, expires_at.isoformat() if expires_at else None)

        if not internal:
            replicate = self._replicate_supplier()
            await replicate(
                method="PUT",
                key=key,
                item=item_model(value=value, version=version, ttl_ms=ttl_ms),
                all_nodes=nodes,
                internal_token=internal_token,
                self_url=self_url,
            )

    async def delete(
        self,
        *,
        key: str,
        internal: bool,
        nodes,
        internal_token: str,
        self_url: str,
    ) -> None:
        if key in self._cache:
            del self._cache[key]
        self._repository.delete(key)

        if not internal:
            replicate = self._replicate_supplier()
            await replicate(
                method="DELETE",
                key=key,
                item=None,
                all_nodes=nodes,
                internal_token=internal_token,
                self_url=self_url,
            )


