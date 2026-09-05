import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.all_models import MarketSnapshot, Stock
from app.services.pulse_engine import PulseEngine
from app.database.seed import BASE_PRICES

# Per-stock price tracking for realistic simulation across calls
_current_prices: dict = {}

# Sector change state (simulate sector-wide moves)
_sector_state: dict = {}


class MarketDataService:

    @staticmethod
    def _get_sector_change(sector: str) -> float:
        """Get a shared sector change for all stocks in the same sector."""
        if sector not in _sector_state:
            _sector_state[sector] = (random.random() - 0.5) * 0.02  # +-1%
        return _sector_state[sector]

    @staticmethod
    def _refresh_sector_changes():
        """Called at the start of each simulator run to refresh sector moves."""
        for sector in list(_sector_state.keys()):
            _sector_state[sector] = (random.random() - 0.5) * 0.02

    @staticmethod
    def ingest(
        db: Session,
        stock_id: int,
        current_price: float,
        previous_price: float,
        volume: int,
        avg_volume: int,
        sector_change: float,
        source: str = "mock",
        user_threshold: float = 5.0,
    ) -> MarketSnapshot:
        """
        Single entry point for all market data ingestion.
        Applies reconciliation rule:
        - If a snapshot with overlapping data_timestamp already exists and prices
          diverge by more than 1%, mark both as stale.
        - Otherwise, mark prior snapshot stale and insert fresh.
        """
        now = datetime.utcnow()

        # Find the most recent non-stale snapshot for this stock
        prior = (
            db.query(MarketSnapshot)
            .filter(MarketSnapshot.stock_id == stock_id, MarketSnapshot.is_stale == False)
            .order_by(MarketSnapshot.received_timestamp.desc())
            .first()
        )

        if prior is not None:
            price_divergence = abs(current_price - prior.price) / prior.price if prior.price else 0
            if price_divergence > 0.01 and prior.data_timestamp and (
                abs((now - prior.data_timestamp).total_seconds()) < 60
            ):
                # Overlapping window with >1% divergence -- mark both stale
                prior.is_stale = True
                db.flush()
                snapshot = MarketSnapshot(
                    stock_id=stock_id,
                    price=current_price,
                    previous_price=previous_price,
                    volume=volume,
                    average_volume=avg_volume,
                    sector_change=sector_change,
                    data_timestamp=now,
                    received_timestamp=now,
                    source=source,
                    is_stale=True,  # Both stale until superseded
                )
            else:
                prior.is_stale = True
                db.flush()
                snapshot = MarketSnapshot(
                    stock_id=stock_id,
                    price=current_price,
                    previous_price=previous_price,
                    volume=volume,
                    average_volume=avg_volume,
                    sector_change=sector_change,
                    data_timestamp=now,
                    received_timestamp=now,
                    source=source,
                    is_stale=False,
                )
        else:
            snapshot = MarketSnapshot(
                stock_id=stock_id,
                price=current_price,
                previous_price=previous_price,
                volume=volume,
                average_volume=avg_volume,
                sector_change=sector_change,
                data_timestamp=now,
                received_timestamp=now,
                source=source,
                is_stale=False,
            )

        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        # Trigger Pulse Engine
        from app.services.change_detector import ChangeDetector
        score = PulseEngine.evaluate(db, snapshot, user_threshold=user_threshold / 100.0)
        ChangeDetector.evaluate(db, snapshot, score)
        return snapshot

    @staticmethod
    def run_mock_simulator(db: Session, specific_stock_id: int = None,
                           current_price: float = None, previous_price: float = None,
                           volume: int = None, avg_volume: int = None,
                           sector_change: float = None, user_threshold: float = 5.0) -> MarketSnapshot:
        """
        Generates realistic snapshots.
        - Specific stock: use supplied values
        - All stocks: drift with occasional dramatic spikes (20% chance per stock)
        """
        if specific_stock_id:
            return MarketDataService.ingest(
                db, specific_stock_id, current_price, previous_price,
                volume, avg_volume, sector_change, "simulator", user_threshold
            )

        MarketDataService._refresh_sector_changes()
        stocks = db.query(Stock).all()
        last_snapshot = None

        for stock in stocks:
            base = BASE_PRICES.get(stock.symbol, 1000.0)
            prev = _current_prices.get(stock.symbol, base)

            # 20% chance of a dramatic spike (5-10% move)
            if random.random() < 0.20:
                spike_pct = random.choice([-1, 1]) * (0.05 + random.random() * 0.05)  # +-5-10%
                curr = prev * (1 + spike_pct)
                avg_v = int(base * 500)  # 500 shares per Rs1 of base price
                # Spike volume too (2-4x)
                v = int(avg_v * (2.0 + random.random() * 2.0))
            else:
                # Normal drift +-0.8%
                drift = (random.random() - 0.5) * 0.016
                curr = prev * (1 + drift)
                avg_v = int(base * 500)
                # Normal volume +-20%
                v = int(avg_v * (0.8 + random.random() * 0.4))

            _current_prices[stock.symbol] = curr
            sec_change = MarketDataService._get_sector_change(stock.sector)

            last_snapshot = MarketDataService.ingest(
                db, stock.id, curr, prev, v, avg_v, sec_change, "simulator_auto", user_threshold
            )

        return last_snapshot

    @staticmethod
    def run_dramatic_simulator(db: Session, spike_count: int = 2, user_threshold: float = 5.0):
        """
        For demo: forcefully spike spike_count random stocks to guarantee CRITICAL alerts.
        Every selected stock gets a 6-9% move and 3-5x volume.
        """
        MarketDataService._refresh_sector_changes()
        stocks = db.query(Stock).all()
        if not stocks:
            return []

        # Pick spike_count random stocks and spike them hard
        spike_stocks = random.sample(stocks, min(spike_count, len(stocks)))
        spiked = []

        for stock in stocks:
            base = BASE_PRICES.get(stock.symbol, 1000.0)
            prev = _current_prices.get(stock.symbol, base)
            avg_v = int(base * 500)

            if stock in spike_stocks:
                idx = spike_stocks.index(stock)
                if idx == 0:
                    # Target score ~93: 6% price move, 2.5x volume
                    spike_pct = random.choice([-1, 1]) * 0.06
                    curr = prev * (1 + spike_pct)
                    v = int(avg_v * 2.5)
                else:
                    # Target score ~78: 5.1% price move, 1.8x volume
                    spike_pct = random.choice([-1, 1]) * 0.051
                    curr = prev * (1 + spike_pct)
                    v = int(avg_v * 1.8)
            else:
                drift = (random.random() - 0.5) * 0.008  # +-0.4% normal
                curr = prev * (1 + drift)
                v = int(avg_v * (0.85 + random.random() * 0.3))

            _current_prices[stock.symbol] = curr
            sec_change = MarketDataService._get_sector_change(stock.sector)

            snapshot = MarketDataService.ingest(
                db, stock.id, curr, prev, v, avg_v, sec_change, "simulator_dramatic", user_threshold
            )
            if stock in spike_stocks:
                spiked.append(snapshot)

        return spiked

    @staticmethod
    def run_yfinance_fetcher(db: Session, user_threshold: float = 5.0):
        """
        Fetches real-time live market data from Yahoo Finance API for all stocks.
        """
        import yfinance as yf
        
        stocks = db.query(Stock).all()
        if not stocks:
            return []

        # Download batch data for performance
        symbols = [f"{stock.symbol}.NS" for stock in stocks]
        try:
            # period="5d" gives us enough history to get previous close and avg volume
            data = yf.download(symbols, period="5d", group_by="ticker", threads=True, progress=False)
        except Exception as e:
            print(f"Failed to download yfinance data: {e}")
            return []

        results = []
        for stock in stocks:
            try:
                ticker_str = f"{stock.symbol}.NS"
                
                # Check if data exists for this ticker
                if len(symbols) == 1:
                    df = data
                else:
                    if ticker_str not in data.columns.levels[0]:
                        continue
                    df = data[ticker_str]
                
                # Drop NaNs
                df = df.dropna()
                if df.empty or len(df) < 2:
                    continue
                
                curr = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2])
                v = int(df['Volume'].iloc[-1])
                avg_v = int(df['Volume'].mean())
                
                sec_change = MarketDataService._get_sector_change(stock.sector)
                
                snapshot = MarketDataService.ingest(
                    db, stock.id, curr, prev, v, avg_v, sec_change, "yfinance", user_threshold
                )
                results.append(snapshot)
                
            except Exception as e:
                print(f"Error parsing yfinance data for {stock.symbol}: {e}")
                
        return results
