import os
from pathlib import Path

# === Environment variables ===
NODE_ID = os.getenv("NODE_ID", "node1")  # "node1" | "node2" | "node3"
NODES = os.getenv(
    "NODES",
    "http://cache-node-1:8000,http://cache-node-2:8000,http://cache-node-3:8000"
).split(",")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "secret")

# === SQLite path (persistence by node) ===
DATA_DIR = Path("./data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "cache.db")

def is_internal_call(incoming_token: str | None) -> bool:
    """
    True if the request comes from another node (to avoid replication loops).
    Args:
        incoming_token: The token of the incoming request.
    Returns:
        True if the request comes from another node, False otherwise.
    """
    return incoming_token == INTERNAL_TOKEN

def self_internal_url() -> str:
    """
    Internal URL of this node according to its NODE_ID.
    Returns:
        The internal URL of this node.
    """
    # node1 -> http://cache-node-1:8000, etc.
    idx = NODE_ID[-1]
    return f"http://cache-node-{idx}:8000"
