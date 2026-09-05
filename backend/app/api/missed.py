from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from datetime import datetime
from app.database.connection import get_db
from app.models.all_models import MeaningfulChange, UserSession, Stock, Watchlist, WatchlistStock
from app.schemas.all_schemas import MeaningfulChangeOut, StockOut
from app.api.deps import get_current_user_id
from typing import List

router = APIRouter()

def _severity_from_score(score: int) -> str:
    if score > 80: return "CRITICAL"
    if score > 60: return "IMPORTANT"
    if score > 30: return "MODERATE"
    return "NORMAL"

@router.get("", response_model=List[MeaningfulChangeOut])
def get_what_you_missed(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    from app.services.change_detector import rank_attention

    session_record = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .first()
    )
    if not session_record:
        session_record = UserSession(user_id=user_id, last_visit_at=datetime.utcnow())
        db.add(session_record)
        db.commit()
        return []

    # Changes since last visit for this user
    changes = (
        db.query(MeaningfulChange)
        .filter(or_(MeaningfulChange.user_id == user_id, MeaningfulChange.user_id == None))
        .filter(MeaningfulChange.created_at >= session_record.last_visit_at)
        .filter(MeaningfulChange.seen_at == None)  # noqa: E711
        .all()
    )

    results = []
    for c in changes:
        stock = db.query(Stock).filter(Stock.id == c.stock_id).first()
        stock_out = None
        if stock:
            stock_out = StockOut(id=stock.id, symbol=stock.symbol,
                                 company_name=stock.company_name, sector=stock.sector)
        severity = _severity_from_score(c.current_score)
        momentum = c.current_score - c.previous_score
        results.append({
            "id": c.id,
            "stock_id": c.stock_id,
            "previous_score": c.previous_score,
            "current_score": c.current_score,
            "created_at": c.created_at,
            "seen_at": c.seen_at,
            "pulse_score_id": c.pulse_score_id,
            "stock": stock_out,
            "severity": severity,
            "momentum": momentum,
            "timestamp": c.created_at.isoformat() if c.created_at else "",
        })

    # rank by severity + momentum
    results = rank_attention(results)
    return results

@router.post("/ack")
def ack_missed(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session_record = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .first()
    )
    now = datetime.utcnow()
    if session_record:
        session_record.last_visit_at = now
    else:
        session_record = UserSession(user_id=user_id, last_visit_at=now)
        db.add(session_record)

    db.query(MeaningfulChange).filter(
        or_(MeaningfulChange.user_id == user_id, MeaningfulChange.user_id == None),
        MeaningfulChange.seen_at == None  # noqa: E711
    ).update({"seen_at": now}, synchronize_session=False)

    db.commit()
    return {"status": "ok", "last_visit_at": now.isoformat()}
