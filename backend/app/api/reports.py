from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.all_models import MeaningfulChange, PulseScore, Stock, QuickGroup, QuickGroupStock
from app.api.deps import get_current_user_id

router = APIRouter()

def _severity_from_score(score: int) -> str:
    if score > 80: return "CRITICAL"
    if score > 60: return "IMPORTANT"
    if score > 30: return "MODERATE"
    return "NORMAL"

@router.get("")
def get_weekly_report(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    since = datetime.utcnow() - timedelta(days=7)

    changes = (
        db.query(MeaningfulChange)
        .filter(or_(MeaningfulChange.user_id == user_id, MeaningfulChange.user_id == None))
        .filter(MeaningfulChange.created_at >= since)
        .all()
    )

    critical = sum(1 for c in changes if _severity_from_score(c.current_score) == "CRITICAL")
    important = sum(1 for c in changes if _severity_from_score(c.current_score) == "IMPORTANT")
    moderate = sum(1 for c in changes if _severity_from_score(c.current_score) == "MODERATE")
    normal = sum(1 for c in changes if _severity_from_score(c.current_score) == "NORMAL")

    threshold_crossings = sum(1 for c in changes if c.current_score > c.previous_score and c.current_score >= 60)
    volume_anomalies = len(changes)  # approximate

    # Top attention stock
    stock_change_counts = {}
    for c in changes:
        stock_change_counts[c.stock_id] = stock_change_counts.get(c.stock_id, 0) + 1
    top_stock_id = max(stock_change_counts, key=stock_change_counts.get) if stock_change_counts else None
    top_stock = db.query(Stock).filter(Stock.id == top_stock_id).first() if top_stock_id else None

    # Most active group
    groups = db.query(QuickGroup).filter(QuickGroup.user_id == user_id).all()
    most_active_group = None
    max_group_changes = 0
    for group in groups:
        group_stock_ids = [gs.stock_id for gs in db.query(QuickGroupStock).filter(QuickGroupStock.quick_group_id == group.id).all()]
        group_changes = sum(1 for c in changes if c.stock_id in group_stock_ids)
        if group_changes > max_group_changes:
            max_group_changes = group_changes
            most_active_group = group.name

    return {
        "period_days": 7,
        "total_changes": len(changes),
        "critical_changes": critical,
        "important_changes": important,
        "moderate_changes": moderate,
        "normal_changes": normal,
        "top_attention_stock": top_stock.symbol if top_stock else None,
        "most_active_group": most_active_group,
        "threshold_crossings": threshold_crossings,
        "volume_anomalies": volume_anomalies,
        "generated_at": datetime.utcnow().isoformat(),
    }
