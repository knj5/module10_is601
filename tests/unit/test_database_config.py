import pytest
from app.database import get_engine

@pytest.fixture(autouse=True)
def clear_engine_cache():
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()

def test_missing_database_configuration_is_explicit(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="Set DATABASE_URL"):
        get_engine()

def test_sqlite_is_not_used_as_a_silent_substitute(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(RuntimeError, match="requires PostgreSQL"):
        get_engine()
