from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request, Depends
from typing import Dict
from datetime import datetime

from .config import NODE_ID, NODES, INTERNAL_TOKEN, is_internal_call, self_internal_url
from .persistence import init_db
from .schemas.cache_item import CacheItem
from .utils.replication import replicate_to_others

from .infrastructure.sqlite_repository import SQLiteCacheRepository
from .domain.conflict_resolution import LastWriterWinsByVersion
from .services.cache_service import CacheService


def create_app() -> FastAPI:
    app = FastAPI(title="Distributed Cache")

    # Wiring
    repository = SQLiteCacheRepository()
    conflict = LastWriterWinsByVersion()

    # Supplier to allow monkeypatching server.main.replicate_to_others in tests
    def replicate_supplier():
        from . import main
        return main.replicate_to_others

    service = CacheService(repository, conflict, replicate_supplier)

    @app.on_event("startup")
    def on_startup():
        init_db()
        service.load_from_repository()

    def get_service() -> CacheService:
        return service

    @app.put("/cache/{key}")
    async def put_item(key: str, item: CacheItem, request: Request, svc: CacheService = Depends(get_service)):
        internal = is_internal_call(request.headers.get("X-Internal-Token"))
        try:
            await svc.put(
                key=key,
                value=item.value,
                version=item.version,
                ttl_ms=item.ttl_ms,
                internal=internal,
                nodes=NODES,
                internal_token=INTERNAL_TOKEN,
                self_url=self_internal_url(),
                item_model=CacheItem,
            )
            return {"status": "stored", "node": NODE_ID}
        except ValueError:
            raise HTTPException(status_code=409, detail="Version conflict")

    @app.get("/cache/{key}")
    def get_item(key: str, svc: CacheService = Depends(get_service)):
        try:
            entry = svc.get(key)
            return {
                "value": entry["value"],
                "version": entry["version"],
                "expires_at": entry["expires_at"].isoformat() if entry["expires_at"] else None,
            }
        except KeyError as err:
            detail = str(err).strip("'")
            raise HTTPException(status_code=404, detail=detail)

    @app.delete("/cache/{key}")
    async def delete_item(key: str, request: Request, svc: CacheService = Depends(get_service)):
        internal = is_internal_call(request.headers.get("X-Internal-Token"))
        await svc.delete(
            key=key,
            internal=internal,
            nodes=NODES,
            internal_token=INTERNAL_TOKEN,
            self_url=self_internal_url(),
        )
        return {"status": "deleted", "node": NODE_ID}

    @app.get("/_health")
    def health():
        return {"node": NODE_ID, "status": "ok"}

    return app


