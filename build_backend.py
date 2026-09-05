import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse\backend"

files = {
    "requirements.txt": """fastapi\nuvicorn[standard]\nsqlalchemy\npsycopg2-binary\npydantic\npydantic-settings\nwebsockets\napscheduler\npython-jose[cryptography]\npasslib[bcrypt]\npython-multipart\n""",
    ".env.example": """DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketpulse\nJWT_SECRET=supersecret123\nFRONTEND_URL=http://localhost:5173\nMARKET_API_URL=mock\nMARKET_API_KEY=mock\n""",
    "app/database/__init__.py": "",
    "app/database/connection.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db") 
# Using SQLite for ease of quick local demo if postgres isn't running, but code is written for postgres

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
}

for filepath, content in files.items():
    full_path = os.path.join(BASE_DIR, filepath.replace("/", "\\\\"))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Backend base files created.")
