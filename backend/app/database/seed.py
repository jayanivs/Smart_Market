from sqlalchemy.orm import Session
from datetime import datetime
from app.models.all_models import (
    User, Stock, Watchlist, WatchlistStock,
    UserSession, SmartWatchPreference
)

SEED_STOCKS = [
    # Technology sector
    {"symbol": "INFY",    "company_name": "Infosys Ltd.",                   "sector": "Technology"},
    {"symbol": "TCS",     "company_name": "Tata Consultancy Services",       "sector": "Technology"},
    {"symbol": "WIPRO",   "company_name": "Wipro Ltd.",                      "sector": "Technology"},
    {"symbol": "TECHM",   "company_name": "Tech Mahindra Ltd.",              "sector": "Technology"},
    # Finance sector
    {"symbol": "HDFCBANK","company_name": "HDFC Bank Ltd.",                  "sector": "Finance"},
    {"symbol": "ICICIBANK","company_name": "ICICI Bank Ltd.",                "sector": "Finance"},
    {"symbol": "SBIN",    "company_name": "State Bank of India",             "sector": "Finance"},
    # Energy sector
    {"symbol": "RELIANCE","company_name": "Reliance Industries Ltd.",        "sector": "Energy"},
    {"symbol": "ONGC",    "company_name": "Oil & Natural Gas Corp.",         "sector": "Energy"},
    {"symbol": "BPCL",    "company_name": "Bharat Petroleum Corp. Ltd.",     "sector": "Energy"},
]

# Realistic base prices for each stock
BASE_PRICES = {
    "INFY":     1540.0,
    "TCS":      3920.0,
    "WIPRO":     480.0,
    "TECHM":     920.0,
    "HDFCBANK": 1620.0,
    "ICICIBANK": 980.0,
    "SBIN":      745.0,
    "RELIANCE": 2870.0,
    "ONGC":      270.0,
    "BPCL":      490.0,
}

def seed_database(db: Session):
    """Idempotent seed — only creates data if it doesn't already exist."""
    # Demo user
    existing_user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
    if existing_user:
        # Already seeded
        return

    user = User(
        name="Demo User",
        email="demo@marketpulse.com",
        password_hash="demo_hashed_password",
    )
    db.add(user)
    db.flush()  # get user.id without committing

    # Seed stocks
    stock_objs = []
    for s in SEED_STOCKS:
        existing = db.query(Stock).filter(Stock.symbol == s["symbol"]).first()
        if not existing:
            stock = Stock(**s)
            db.add(stock)
            db.flush()
            stock_objs.append(stock)
        else:
            stock_objs.append(existing)

    # Default watchlist
    wl = Watchlist(user_id=user.id, name="My Watchlist")
    db.add(wl)
    db.flush()

    # Add all stocks to the watchlist
    for stock in stock_objs:
        ws = WatchlistStock(watchlist_id=wl.id, stock_id=stock.id)
        db.add(ws)

    # User session
    db.add(UserSession(user_id=user.id, last_visit_at=datetime.utcnow()))

    # Smart watch preferences (medium sensitivity)
    db.add(SmartWatchPreference(
        user_id=user.id,
        enabled=True,
        price_threshold=5.0,
        volume_threshold=2.0,
        sensitivity="MEDIUM",
    ))

    db.commit()
    print("[Seed] Database seeded with demo user, 10 stocks, 1 watchlist.")
