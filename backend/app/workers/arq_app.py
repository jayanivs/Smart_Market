import os
from arq.connections import RedisSettings
from app.database.connection import SessionLocal
from app.models.all_models import MarketSnapshot, PulseScore

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def evaluate_market_snapshot_task(ctx, snapshot_id: int, score_id: int):
    """ARQ Worker background task for evaluating user thresholds and changes."""
    from app.services.change_detector import ChangeDetector
    db = SessionLocal()
    try:
        snapshot = db.query(MarketSnapshot).filter(MarketSnapshot.id == snapshot_id).first()
        score = db.query(PulseScore).filter(PulseScore.id == score_id).first()
        if snapshot and score:
            ChangeDetector.evaluate(db, snapshot, score)
    finally:
        db.close()

class WorkerSettings:
    functions = [evaluate_market_snapshot_task]
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
