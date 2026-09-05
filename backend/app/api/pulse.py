from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.connection import get_db
from app.models.all_models import PulseScore, PulseExplanation, Watchlist, WatchlistStock, MarketSnapshot, Stock
from app.schemas.all_schemas import PulseScoreOut, PulseExplanationOut, SnapshotInfo, StockOut
from typing import List, Optional
from app.services.change_detector import rank_attention
from app.api.deps import get_current_user_id

router = APIRouter()


def _enrich_score(db: Session, score: PulseScore) -> dict:
    """Build a dict matching PulseScoreOut by joining snapshot and stock data."""
    stock = db.query(Stock).filter(Stock.id == score.stock_id).first()
    snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == score.stock_id)
        .order_by(desc(MarketSnapshot.received_timestamp))
        .first()
    )
    explanations = (
        db.query(PulseExplanation)
        .filter(PulseExplanation.pulse_score_id == score.id)
        .all()
    )

    snapshot_info = None
    if snapshot:
        snapshot_info = SnapshotInfo(
            price=snapshot.price,
            previous_price=snapshot.previous_price,
            volume=snapshot.volume,
            average_volume=snapshot.average_volume,
            is_stale=snapshot.is_stale,
            data_timestamp=snapshot.data_timestamp,
        )

    stock_out = None
    if stock:
        stock_out = StockOut(id=stock.id, symbol=stock.symbol,
                             company_name=stock.company_name, sector=stock.sector)

    return {
        "id": score.id,
        "stock_id": score.stock_id,
        "score": score.score,
        "price_signal": score.price_signal,
        "volume_signal": score.volume_signal,
        "sector_signal": score.sector_signal,
        "threshold_signal": score.threshold_signal,
        "severity": score.severity,
        "momentum": score.momentum,
        "timestamp": score.timestamp.isoformat() if score.timestamp else "",
        "explanations": explanations,
        "stock": stock_out,
        "snapshot": snapshot_info,
    }


@router.get("", response_model=List[PulseScoreOut])
def get_latest_pulse(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    wl_stocks = (
        db.query(WatchlistStock.stock_id)
        .join(Watchlist)
        .filter(Watchlist.user_id == user_id)
        .all()
    )
    stock_ids = list({ws[0] for ws in wl_stocks})

    results = []
    for sid in stock_ids:
        score = (
            db.query(PulseScore)
            .filter(PulseScore.stock_id == sid)
            .order_by(desc(PulseScore.timestamp))
            .first()
        )
        if score:
            results.append(_enrich_score(db, score))

    results = rank_attention(results)
    
    # We must convert timestamps back to datetime for pydantic parsing
    from datetime import datetime
    for r in results:
        if isinstance(r["timestamp"], str) and r["timestamp"]:
            r["timestamp"] = datetime.fromisoformat(r["timestamp"])

    return results


@router.get("/{stock_id}/why")
def get_pulse_why(stock_id: int, db: Session = Depends(get_db)):
    score = (
        db.query(PulseScore)
        .filter(PulseScore.stock_id == stock_id)
        .order_by(desc(PulseScore.timestamp))
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="No pulse score found for this stock")
    explanations = (
        db.query(PulseExplanation)
        .filter(PulseExplanation.pulse_score_id == score.id)
        .all()
    )
    return {
        "score": score.score,
        "severity": score.severity,
        "momentum": score.momentum,
        "reasons": [
            {"type": exp.reason_type, "message": exp.message, "impact": exp.impact}
            for exp in explanations
        ]
    }


@router.get("/{stock_id}/history", response_model=List[PulseScoreOut])
def get_pulse_history(stock_id: int, limit: int = 20, db: Session = Depends(get_db)):
    scores = (
        db.query(PulseScore)
        .filter(PulseScore.stock_id == stock_id)
        .order_by(desc(PulseScore.timestamp))
        .limit(limit)
        .all()
    )
    results = [_enrich_score(db, s) for s in scores]
    
    from datetime import datetime
    for r in results:
        if isinstance(r["timestamp"], str) and r["timestamp"]:
            r["timestamp"] = datetime.fromisoformat(r["timestamp"])
            
    # Return in chronological order for sparkline
    results.reverse()
    return results
