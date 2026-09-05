from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.all_models import Watchlist, WatchlistStock, Stock
from app.schemas.all_schemas import (
    WatchlistCreate, WatchlistOut, WatchlistAddStock,
    WatchlistRename, WatchlistReorder,
)
from app.api.deps import get_current_user_id

router = APIRouter()


def _build_watchlist_out(db: Session, wl: Watchlist) -> WatchlistOut:
    """Helper: load stocks ordered by position, return WatchlistOut."""
    wl_stocks = (
        db.query(Stock)
        .join(WatchlistStock)
        .filter(WatchlistStock.watchlist_id == wl.id)
        .order_by(WatchlistStock.position)
        .all()
    )
    return WatchlistOut(
        id=wl.id,
        name=wl.name,
        stocks=[
            {"id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector}
            for s in wl_stocks
        ],
    )


# ── GET /watchlists ───────────────────────────────────────────────────────────

@router.get("", response_model=list[WatchlistOut])
def get_watchlists(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    return [_build_watchlist_out(db, wl) for wl in watchlists]


# ── POST /watchlists ──────────────────────────────────────────────────────────

@router.post("", response_model=WatchlistOut)
def create_watchlist(
    wl_in: WatchlistCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = Watchlist(user_id=user_id, name=wl_in.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return WatchlistOut(id=wl.id, name=wl.name, stocks=[])


# ── PATCH /watchlists/{watchlist_id} (rename) ─────────────────────────────────

@router.patch("/{watchlist_id}", response_model=WatchlistOut)
def rename_watchlist(
    watchlist_id: int,
    body: WatchlistRename,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    wl.name = body.name
    db.commit()
    db.refresh(wl)
    return _build_watchlist_out(db, wl)


# ── DELETE /watchlists/{watchlist_id} ─────────────────────────────────────────

@router.delete("/{watchlist_id}")
def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # Explicitly delete related WatchlistStock rows to avoid IntegrityError
    db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).delete()
    
    db.delete(wl)
    db.commit()
    return {"status": "ok"}


# ── POST /watchlists/{watchlist_id}/stocks ────────────────────────────────────

@router.post("/{watchlist_id}/stocks", response_model=WatchlistOut)
def add_stock_to_watchlist(
    watchlist_id: int,
    stock_in: WatchlistAddStock,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Assign next available position
    existing_count = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == wl.id
    ).count()
    ws = WatchlistStock(watchlist_id=wl.id, stock_id=stock_in.stock_id, position=existing_count)
    db.add(ws)
    db.commit()
    return _build_watchlist_out(db, wl)


# ── PATCH /watchlists/{watchlist_id}/stocks/reorder ──────────────────────────

@router.patch("/{watchlist_id}/stocks/reorder", response_model=WatchlistOut)
def reorder_watchlist_stocks(
    watchlist_id: int,
    body: WatchlistReorder,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Validate all stock_ids belong to this watchlist
    existing_stock_ids = {
        ws.stock_id
        for ws in db.query(WatchlistStock).filter(
            WatchlistStock.watchlist_id == watchlist_id
        ).all()
    }
    unknown = set(body.stock_ids) - existing_stock_ids
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown stock_id(s) not in watchlist: {sorted(unknown)}",
        )

    # Update positions
    for pos, sid in enumerate(body.stock_ids):
        db.query(WatchlistStock).filter(
            WatchlistStock.watchlist_id == watchlist_id,
            WatchlistStock.stock_id == sid,
        ).update({"position": pos})
    db.commit()
    return _build_watchlist_out(db, wl)


# ── DELETE /watchlists/{watchlist_id}/stocks/{stock_id} ──────────────────────

@router.delete("/{watchlist_id}/stocks/{stock_id}")
def remove_stock(
    watchlist_id: int,
    stock_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    ws = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist_id,
        WatchlistStock.stock_id == stock_id,
    ).first()
    if ws:
        db.delete(ws)
        db.commit()
    return {"status": "ok"}
