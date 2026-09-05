from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db") 
# Using SQLite for ease of quick local demo if postgres isn't running, but code is written for postgres

engine_kwargs = {"connect_args": {"check_same_thread": False}} if "sqlite" in DATABASE_URL else {}
if DATABASE_URL == "sqlite:///:memory:":
    from sqlalchemy.pool import StaticPool
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
