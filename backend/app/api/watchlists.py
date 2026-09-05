from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.all_models import Watchlist, WatchlistStock, Stock
from app.schemas.all_schemas import WatchlistCreate, WatchlistOut, WatchlistAddStock
from app.api.deps import get_current_user_id

router = APIRouter()

@router.get("", response_model=list[WatchlistOut])
def get_watchlists(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    result = []
    for wl in watchlists:
        wl_stocks = db.query(Stock).join(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).all()
        wl_out = WatchlistOut(
            id=wl.id,
            name=wl.name,
            stocks=[{"id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector} for s in wl_stocks]
        )
        result.append(wl_out)
    return result

@router.post("", response_model=WatchlistOut)
def create_watchlist(wl_in: WatchlistCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    wl = Watchlist(user_id=user_id, name=wl_in.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return WatchlistOut(id=wl.id, name=wl.name, stocks=[])

@router.post("/{watchlist_id}/stocks", response_model=WatchlistOut)
def add_stock_to_watchlist(
    watchlist_id: int,
    stock_in: WatchlistAddStock,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    ws = WatchlistStock(watchlist_id=wl.id, stock_id=stock_in.stock_id)
    db.add(ws)
    db.commit()
    
    wl_stocks = db.query(Stock).join(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).all()
    return WatchlistOut(
        id=wl.id,
        name=wl.name,
        stocks=[{"id": s.id, "symbol": s.symbol, "company_name": s.company_name, "sector": s.sector} for s in wl_stocks]
    )

@router.delete("/{watchlist_id}/stocks/{stock_id}")
def remove_stock(
    watchlist_id: int,
    stock_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == user_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    ws = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist_id,
        WatchlistStock.stock_id == stock_id
    ).first()
    if ws:
        db.delete(ws)
        db.commit()
    return {"status": "ok"}
