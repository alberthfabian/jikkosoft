"""
    Main module for the cache system.
"""
# Ensure replicate_to_others is a module-level attribute for monkeypatch in tests
from .utils import replication as _replication
replicate_to_others = _replication.replicate_to_others

from .app_factory import create_app

# FastAPI app created via factory with injected patterns (Repository, Service, Strategy)
app = create_app()
