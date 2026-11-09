"""PostgreSQL connections shared by the API and command line initializer."""
import os
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase):
    pass

@lru_cache
def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL to the Module 10 PostgreSQL database")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        raise RuntimeError("This project requires PostgreSQL")
    parsed = parsed.set(drivername="postgresql+psycopg")
    return create_engine(parsed, pool_pre_ping=True, connect_args={"connect_timeout": 10})

def init_db():
    from app import models  # Register model metadata before creating tables.
    Base.metadata.create_all(get_engine())

def get_db():
    with Session(get_engine()) as session:
        yield session

if __name__ == "__main__":
    # Import the canonical module so models share its Base when run with -m.
    from app.database import init_db as initialize
    initialize()
    print("Module 10 database tables are ready")
