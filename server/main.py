from .utils.replication import replicate_to_others  # re-export for tests monkeypatch
from .app_factory import create_app

# FastAPI app created via factory with injected patterns (Repository, Service, Strategy)
app = create_app()
