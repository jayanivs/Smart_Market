from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.all_schemas import MarketChangeSimulate
from app.services.market_data import MarketDataService
from app.models.all_models import SmartWatchPreference, Stock
from app.api.deps import get_current_user_id

router = APIRouter()


def _get_user_threshold(db: Session, user_id: int = 1) -> float:
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id
    ).first()
    return prefs.price_threshold if prefs else 5.0


@router.post("/market-change")
def simulate_market_change(
    data: MarketChangeSimulate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    threshold = _get_user_threshold(db, user_id)
    snapshot = MarketDataService.run_mock_simulator(
        db,
        specific_stock_id=data.stock_id,
        current_price=data.current_price,
        previous_price=data.previous_price,
        volume=data.volume,
        avg_volume=data.avg_volume,
        sector_change=data.sector_change,
        user_threshold=threshold,
    )
    return {"status": "success", "stock_id": snapshot.stock_id if snapshot else None}


@router.post("/trigger-random")
def trigger_random(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """
    Runs a dramatic simulation that guarantees 2 stocks get spiked hard (6-9% move,
    3-5x volume) — designed to produce CRITICAL/IMPORTANT alerts for the demo.
    """
    threshold = _get_user_threshold(db, user_id)
    spiked = MarketDataService.run_dramatic_simulator(db, spike_count=2, user_threshold=threshold)
    return {
        "status": "success",
        "message": f"Simulated dramatic market changes. {len(spiked)} stocks spiked.",
        "spiked_stock_ids": [s.stock_id for s in spiked],
    }


@router.post("/trigger-all")
def trigger_all(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Runs the full simulator on all stocks with natural drift + occasional spikes."""
    threshold = _get_user_threshold(db, user_id)
    MarketDataService.run_mock_simulator(db, user_threshold=threshold)
    return {"status": "success", "message": "Random market changes generated for all stocks"}

@router.post("/trigger-live")
def trigger_live(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Fetches real-time market data from Yahoo Finance for NSE stocks."""
    threshold = _get_user_threshold(db, user_id)
    results = MarketDataService.run_yfinance_fetcher(db, user_threshold=threshold)
    return {
        "status": "success",
        "message": f"Fetched live data for {len(results)} stocks.",
    }

@router.post("/spike/{symbol}")
def spike_stock(symbol: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """
    Force a dramatic spike on a specific stock by symbol.
    Guaranteed 6-9% price move and 3-5x volume — produces CRITICAL alert for demo.
    """
    import random
    from app.database.seed import BASE_PRICES
    from app.services.market_data import _current_prices, _sector_state
    
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    threshold = _get_user_threshold(db, user_id)
    base = BASE_PRICES.get(stock.symbol, 1000.0)
    prev = _current_prices.get(stock.symbol, base)
    avg_v = int(base * 500)
    
    spike_pct = random.choice([-1, 1]) * (0.06 + random.random() * 0.03)  # +-6-9%
    curr = prev * (1 + spike_pct)
    v = int(avg_v * (3.0 + random.random() * 2.0))  # 3-5x volume
    _current_prices[stock.symbol] = curr
    
    if stock.sector not in _sector_state:
        _sector_state[stock.sector] = (random.random() - 0.5) * 0.02
    sec_change = _sector_state[stock.sector]
    
    snapshot = MarketDataService.ingest(
        db, stock.id, curr, prev, v, avg_v, sec_change, "simulator_spike", threshold
    )
    
    # Get the resulting pulse score
    from sqlalchemy import desc
    from app.models.all_models import PulseScore
    latest_score = db.query(PulseScore).filter(
        PulseScore.stock_id == stock.id
    ).order_by(desc(PulseScore.timestamp)).first()
    
    return {
        "status": "success",
        "symbol": stock.symbol,
        "stock_id": stock.id,
        "price_before": round(prev, 2),
        "price_after": round(curr, 2),
        "change_pct": round(spike_pct * 100, 2),
        "volume": v,
        "pulse_score": latest_score.score if latest_score else None,
        "severity": latest_score.severity if latest_score else None,
    }
