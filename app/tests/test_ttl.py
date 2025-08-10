"""
    Test the TTL expiration.
"""
import time
from fastapi.testclient import TestClient
from app.main import app

def test_ttl_expiration(monkeypatch):
    """
    Test the TTL expiration.
    Args:
        monkeypatch: The monkeypatch object.
    """
    # Mock replication
    async def no_replicate(*args, **kwargs): 
        return None
    monkeypatch.setattr("app.main.replicate_to_others", no_replicate)

    client = TestClient(app)

    # TTL short (100 ms)
    r = client.put("/cache/temp", json={"value": {"temp": True}, "version": 1, "ttl_ms": 100})
    assert r.status_code == 200

    # Immediately: exists
    r = client.get("/cache/temp")
    assert r.status_code == 200

    # Wait for it to expire
    time.sleep(0.2)

    # Should give 404 (Expired)
    r = client.get("/cache/temp")
    assert r.status_code == 404
    assert r.json()["detail"] in ("Expired", "Not found")
