from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from datetime import datetime
from app.database.connection import get_db
from app.models.all_models import MeaningfulChange, Stock, PulseScore, UserSession
from app.api.deps import get_current_user_id
from typing import List

router = APIRouter()

def _severity_from_score(score: int) -> str:
    if score > 80: return "CRITICAL"
    if score > 60: return "IMPORTANT"
    if score > 30: return "MODERATE"
    return "NORMAL"

@router.get("")
def get_notifications(
    filter: str = "ALL",
    limit: int = 50,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Return recent meaningful changes as notifications for the current user."""
    changes = (
        db.query(MeaningfulChange)
        .filter(or_(MeaningfulChange.user_id == user_id, MeaningfulChange.user_id == None))
        .order_by(desc(MeaningfulChange.created_at))
        .limit(200)
        .all()
    )

    results = []
    for c in changes:
        severity = _severity_from_score(c.current_score)
        if filter != "ALL" and severity != filter and filter != "INFO":
            continue
        if filter == "INFO" and severity not in ("MODERATE", "NORMAL"):
            continue

        stock = db.query(Stock).filter(Stock.id == c.stock_id).first()
        stock_symbol = stock.symbol if stock else f"#{c.stock_id}"
        stock_name = stock.company_name if stock else ""

        delta = c.current_score - c.previous_score
        if delta > 0:
            message = f"{stock_symbol} attention increased from {c.previous_score} to {c.current_score}"
        else:
            message = f"{stock_symbol} attention decreased from {c.previous_score} to {c.current_score}"

        results.append({
            "id": c.id,
            "stock_id": c.stock_id,
            "stock_symbol": stock_symbol,
            "stock_name": stock_name,
            "previous_score": c.previous_score,
            "current_score": c.current_score,
            "severity": severity,
            "message": message,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "seen_at": c.seen_at.isoformat() if c.seen_at else None,
            "is_read": c.seen_at is not None,
        })

    return results[:limit]

@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    change = db.query(MeaningfulChange).filter(MeaningfulChange.id == notification_id).first()
    if not change:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    if not change.seen_at:
        change.seen_at = datetime.utcnow()
        db.commit()
    return {"status": "ok"}

@router.post("/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    now = datetime.utcnow()
    db.query(MeaningfulChange).filter(
        or_(MeaningfulChange.user_id == user_id, MeaningfulChange.user_id == None),
        MeaningfulChange.seen_at == None  # noqa: E711
    ).update({"seen_at": now}, synchronize_session=False)
    
    # Also update session last_visit
    session = db.query(UserSession).filter(UserSession.user_id == user_id).first()
    if session:
        session.last_visit_at = now
    else:
        db.add(UserSession(user_id=user_id, last_visit_at=now))
    
    db.commit()
    return {"status": "ok", "marked_at": now.isoformat()}
