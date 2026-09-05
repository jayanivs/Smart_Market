"""
Market data API using Financial Modeling Prep (FMP) API.
Free API key: https://financialmodelingprep.com/developer/docs/
Set env var: FMP_API_KEY=your_key (falls back to 'demo' which is limited)
"""
import os
import requests
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.all_models import SmartWatchPreference, Stock
from app.services.market_data import MarketDataService
from pydantic import BaseModel
from typing import List, Optional
from app.api.deps import get_current_user_id

router = APIRouter()

FMP_API_KEY = os.getenv("FMP_API_KEY", "demo")
FMP_BASE = "https://financialmodelingprep.com/api/v3"

# Map our symbols to NSE format for FMP
def _to_fmp_symbol(symbol: str) -> str:
    return f"{symbol}.NS"

def _fmp_get(endpoint: str, params: dict = None) -> dict | list:
    url = f"{FMP_BASE}/{endpoint}"
    p = {"apikey": FMP_API_KEY}
    if params:
        p.update(params)
    resp = requests.get(url, params=p, timeout=10)
    resp.raise_for_status()
    return resp.json()


class QuoteOut(BaseModel):
    symbol: str
    company_name: str
    sector: str
    price: float
    previous_close: float
    open: float
    high: float
    low: float
    volume: int
    avg_volume: int
    change: float
    change_pct: float
    week_52_high: float
    week_52_low: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None


class MarketDepthLevel(BaseModel):
    price: float
    quantity: int
    orders: int


class MarketDepthOut(BaseModel):
    symbol: str
    ltp: float
    buy: List[MarketDepthLevel]
    sell: List[MarketDepthLevel]


class IndexOut(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float


def _get_user_threshold(db: Session, user_id: int = 1) -> float:
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id
    ).first()
    return prefs.price_threshold if prefs else 5.0


@router.get("/indices", response_model=List[IndexOut])
def get_market_indices():
    """Fetch major Indian market indices."""
    try:
        indices = [
            ("^NSEI", "NIFTY 50"),
            ("^BSESN", "SENSEX"),
            ("^NSEBANK", "BANK NIFTY"),
        ]
        results = []
        symbols_str = ",".join(sym for sym, _ in indices)
        data = _fmp_get(f"quote/{symbols_str}")
        
        name_map = {sym: name for sym, name in indices}
        if isinstance(data, list):
            for item in data:
                sym = item.get("symbol", "")
                results.append(IndexOut(
                    symbol=sym,
                    name=name_map.get(sym, sym),
                    price=item.get("price", 0),
                    change=item.get("change", 0),
                    change_pct=item.get("changesPercentage", 0),
                ))
        return results
    except Exception as e:
        # Return placeholder on failure (market might be closed)
        return [
            IndexOut(symbol="^NSEI", name="NIFTY 50", price=0, change=0, change_pct=0),
            IndexOut(symbol="^BSESN", name="SENSEX", price=0, change=0, change_pct=0),
            IndexOut(symbol="^NSEBANK", name="BANK NIFTY", price=0, change=0, change_pct=0),
        ]


@router.get("/quote/{symbol}", response_model=QuoteOut)
def get_quote(symbol: str, db: Session = Depends(get_db)):
    """Fetch live quote from FMP for a single stock."""
    stock_db = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock_db:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    fmp_sym = _to_fmp_symbol(symbol.upper())
    try:
        data = _fmp_get(f"quote/{fmp_sym}")
        if not data or not isinstance(data, list) or len(data) == 0:
            raise HTTPException(status_code=503, detail="No data from FMP")
        q = data[0]
        return QuoteOut(
            symbol=symbol.upper(),
            company_name=stock_db.company_name,
            sector=stock_db.sector,
            price=q.get("price", 0),
            previous_close=q.get("previousClose", 0),
            open=q.get("open", 0),
            high=q.get("dayHigh", 0),
            low=q.get("dayLow", 0),
            volume=q.get("volume", 0),
            avg_volume=q.get("avgVolume", 0),
            change=q.get("change", 0),
            change_pct=q.get("changesPercentage", 0),
            week_52_high=q.get("yearHigh", 0),
            week_52_low=q.get("yearLow", 0),
            market_cap=q.get("marketCap"),
            pe_ratio=q.get("pe"),
            eps=q.get("eps"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"FMP error: {str(e)}")


@router.get("/quotes", response_model=List[QuoteOut])
def get_quotes_batch(symbols: str, db: Session = Depends(get_db)):
    """Fetch live quotes for multiple stocks (comma-separated symbols)."""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    fmp_symbols = ",".join(_to_fmp_symbol(s) for s in symbol_list)

    try:
        data = _fmp_get(f"quote/{fmp_symbols}")
        if not isinstance(data, list):
            return []

        stock_map = {s.symbol: s for s in db.query(Stock).filter(Stock.symbol.in_(symbol_list)).all()}
        results = []
        for q in data:
            raw_sym = q.get("symbol", "")
            # Strip .NS suffix
            sym = raw_sym.replace(".NS", "").upper()
            stock_db = stock_map.get(sym)
            results.append(QuoteOut(
                symbol=sym,
                company_name=stock_db.company_name if stock_db else sym,
                sector=stock_db.sector if stock_db else "Unknown",
                price=q.get("price", 0),
                previous_close=q.get("previousClose", 0),
                open=q.get("open", 0),
                high=q.get("dayHigh", 0),
                low=q.get("dayLow", 0),
                volume=q.get("volume", 0),
                avg_volume=q.get("avgVolume", 0),
                change=q.get("change", 0),
                change_pct=q.get("changesPercentage", 0),
                week_52_high=q.get("yearHigh", 0),
                week_52_low=q.get("yearLow", 0),
                market_cap=q.get("marketCap"),
                pe_ratio=q.get("pe"),
                eps=q.get("eps"),
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"FMP error: {str(e)}")


@router.get("/depth/{symbol}", response_model=MarketDepthOut)
def get_market_depth(symbol: str, db: Session = Depends(get_db)):
    """
    Simulated market depth (FMP doesn't provide L2 data).
    Generates realistic bid/ask spread around live price.
    """
    import random
    fmp_sym = _to_fmp_symbol(symbol.upper())
    ltp = 100.0
    try:
        data = _fmp_get(f"quote/{fmp_sym}")
        if data and isinstance(data, list):
            ltp = float(data[0].get("price", 100.0))
    except Exception:
        pass

    spread = max(ltp * 0.0005, 0.05)
    buy_levels = []
    sell_levels = []
    for i in range(5):
        buy_price = round(ltp - spread * (i + 1), 2)
        sell_price = round(ltp + spread * (i + 1), 2)
        qty_mult = max(1, int(ltp / 100))
        buy_levels.append(MarketDepthLevel(
            price=buy_price,
            quantity=random.randint(100, 5000) * qty_mult,
            orders=random.randint(1, 25)
        ))
        sell_levels.append(MarketDepthLevel(
            price=sell_price,
            quantity=random.randint(100, 5000) * qty_mult,
            orders=random.randint(1, 25)
        ))

    return MarketDepthOut(symbol=symbol.upper(), ltp=ltp, buy=buy_levels, sell=sell_levels)


@router.post("/fetch-live")
def fetch_live_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Trigger background fetch of FMP data -> pulse engine."""
    threshold = _get_user_threshold(db, user_id)
    background_tasks.add_task(_run_fmp_fetcher, db, threshold)
    return {"status": "fetching", "message": "Live FMP data fetch started"}


def _run_fmp_fetcher(db: Session, user_threshold: float = 5.0):
    """Background task: fetch all watchlist stock prices from FMP and push through pipeline."""
    try:
        stocks = db.query(Stock).all()
        if not stocks:
            return
        fmp_symbols = ",".join(_to_fmp_symbol(s.symbol) for s in stocks)
        data = _fmp_get(f"quote/{fmp_symbols}")
        if not isinstance(data, list):
            return
        
        price_map = {}
        for q in data:
            raw = q.get("symbol", "")
            sym = raw.replace(".NS", "").upper()
            price_map[sym] = {
                "price": q.get("price", 0),
                "prev": q.get("previousClose", 0),
                "volume": q.get("volume", 0),
                "avg_volume": q.get("avgVolume", 0),
            }

        for stock in stocks:
            d = price_map.get(stock.symbol)
            if not d or d["price"] == 0:
                continue
            from app.services.market_data import MarketDataService, _sector_state
            import random
            if stock.sector not in _sector_state:
                _sector_state[stock.sector] = (random.random() - 0.5) * 0.02
            sec_change = _sector_state[stock.sector]
            MarketDataService.ingest(
                db, stock.id,
                d["price"], d["prev"],
                d["volume"], max(d["avg_volume"], 1),
                sec_change, "fmp", user_threshold
            )
    except Exception as e:
        print(f"FMP background fetch error: {e}")
