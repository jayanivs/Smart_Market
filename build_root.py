import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse"

readme_content = """# MARKET PULSE
> A watchlist that watches for you.

## Overview
Market Pulse is an intelligent stock watchlist application that automatically detects meaningful market changes based on user preferences. It provides real-time alerts and attention prioritization.

## Architecture
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + PostgreSQL (SQLAlchemy) + WebSockets
- **Intelligence**: Custom Pulse Engine (determines attention score 0-100)

## Directory Structure
- `/backend`: FastAPI Python backend
- `/frontend`: React application

## Setup Instructions

### Backend Setup
1. `cd backend`
2. `python -m venv venv`
3. Activate venv: `.\\venv\\Scripts\\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. Ensure PostgreSQL is running. Copy `.env.example` to `.env` and configure `DATABASE_URL`.
6. Run server: `uvicorn main:app --reload`
*(Note: A sqlite fallback is included in connection.py for demo purposes if Postgres is unavailable)*

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## DEMO FLOW
1. Open the dashboard.
2. Click "Simulate Market Change"
3. Observe the Pulse Score update from 61 to 93 in real-time via WebSockets.
"""

files = {
    "README.md": readme_content,
}

for filepath, content in files.items():
    full_path = os.path.join(BASE_DIR, filepath.replace("/", "\\\\"))
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Root files created.")
