from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.all_models import QuickGroup, QuickGroupStock, Stock
from app.schemas.all_schemas import QuickGroupCreate, QuickGroupUpdate
from app.api.deps import get_current_user_id

router = APIRouter()

def _build_out(db: Session, group: QuickGroup) -> dict:
    stocks = (
        db.query(Stock)
        .join(QuickGroupStock, Stock.id == QuickGroupStock.stock_id)
        .filter(QuickGroupStock.quick_group_id == group.id)
        .all()
    )
    return {
        "id": group.id,
        "name": group.name,
        "sensitivity": group.sensitivity,
        "auto_watch": group.auto_watch,
        "stocks": [{"id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector} for s in stocks],
    }

@router.get("")
def get_quick_groups(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    groups = db.query(QuickGroup).filter(QuickGroup.user_id == user_id).all()
    return [_build_out(db, g) for g in groups]

@router.post("")
def create_quick_group(body: QuickGroupCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if body.stock_ids:
        sectors = [db.query(Stock).filter(Stock.id == sid).first() for sid in body.stock_ids]
        sector_counts = {}
        for s in sectors:
            if s:
                sector_counts[s.sector] = sector_counts.get(s.sector, 0) + 1
        dominant = max(sector_counts, key=sector_counts.get) if sector_counts else None
        auto_name = body.name if body.name else (f"{dominant} Group" if dominant and len(set(sector_counts)) == 1 else "Mixed Group")
    else:
        auto_name = body.name or "New Group"

    group = QuickGroup(user_id=user_id, name=auto_name, sensitivity=body.sensitivity, auto_watch=body.auto_watch)
    db.add(group)
    db.commit()
    db.refresh(group)

    for stock_id in body.stock_ids:
        db.add(QuickGroupStock(quick_group_id=group.id, stock_id=stock_id))
    db.commit()
    return _build_out(db, group)

@router.patch("/{group_id}")
def update_quick_group(group_id: int, body: QuickGroupUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    group = db.query(QuickGroup).filter(QuickGroup.id == group_id, QuickGroup.user_id == user_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if body.sensitivity is not None:
        group.sensitivity = body.sensitivity
    if body.auto_watch is not None:
        group.auto_watch = body.auto_watch
    db.commit()
    return _build_out(db, group)

@router.delete("/{group_id}")
def delete_quick_group(group_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    group = db.query(QuickGroup).filter(QuickGroup.id == group_id, QuickGroup.user_id == user_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(group)
    db.commit()
    return {"status": "deleted"}
