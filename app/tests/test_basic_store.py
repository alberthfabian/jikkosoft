"""
    Test the basic store operations.
"""
from fastapi.testclient import TestClient
from app.main import app

def test_put_get_delete(monkeypatch):
    """
    Test the basic store operations.
    Args:
        monkeypatch: The monkeypatch object.
    """
    # Avoid replicating in tests
    async def no_replicate(*args, **kwargs): 
        return None
    monkeypatch.setattr("app.main.replicate_to_others", no_replicate)

    client = TestClient(app)

    # PUT
    r = client.put("/cache/k1", json={"value": {"x": 1}, "version": 1, "ttl_ms": 300000})
    assert r.status_code == 200

    # GET
    r = client.get("/cache/k1")
    assert r.status_code == 200
    body = r.json()
    assert body["value"]["x"] == 1
    assert body["version"] == 1

    # conflict (version less or equal)
    r = client.put("/cache/k1", json={"value": {"x": 2}, "version": 1})
    assert r.status_code == 409

    # DELETE
    r = client.delete("/cache/k1")
    assert r.status_code == 200
    r = client.get("/cache/k1")
    assert r.status_code == 404
