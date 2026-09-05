import sys
sys.path.insert(0, '.')

from app.database.connection import engine, Base, SessionLocal
from app.models.all_models import Stock, User, Watchlist, WatchlistStock, UserSession, SmartWatchPreference
Base.metadata.create_all(bind=engine)
db = SessionLocal()

SEED_STOCKS = [
    {"symbol": "INFY",     "company_name": "Infosys Ltd.",                 "sector": "Technology"},
    {"symbol": "TCS",      "company_name": "Tata Consultancy Services",    "sector": "Technology"},
    {"symbol": "WIPRO",    "company_name": "Wipro Ltd.",                   "sector": "Technology"},
    {"symbol": "TECHM",    "company_name": "Tech Mahindra Ltd.",           "sector": "Technology"},
    {"symbol": "HDFCBANK", "company_name": "HDFC Bank Ltd.",               "sector": "Finance"},
    {"symbol": "ICICIBANK","company_name": "ICICI Bank Ltd.",              "sector": "Finance"},
    {"symbol": "SBIN",     "company_name": "State Bank of India",          "sector": "Finance"},
    {"symbol": "RELIANCE", "company_name": "Reliance Industries Ltd.",     "sector": "Energy"},
    {"symbol": "ONGC",     "company_name": "Oil and Natural Gas Corp.",    "sector": "Energy"},
    {"symbol": "BPCL",     "company_name": "Bharat Petroleum Corp. Ltd.",  "sector": "Energy"},
]

for s in SEED_STOCKS:
    existing = db.query(Stock).filter(Stock.symbol == s["symbol"]).first()
    if not existing:
        stock = Stock(**s)
        db.add(stock)
        print("Added: " + s["symbol"])
    else:
        print("Exists: " + s["symbol"])

db.commit()
all_stocks = db.query(Stock).all()
print("Total stocks: " + str(len(all_stocks)))

user = db.query(User).filter(User.email == "demo@marketpulse.com").first()
if not user:
    user = User(name="Demo User", email="demo@marketpulse.com", password_hash="demo")
    db.add(user)
    db.commit()
    db.refresh(user)
    print("Created user: " + str(user.id))
else:
    print("User exists: " + str(user.id))

wl = db.query(Watchlist).filter(Watchlist.user_id == user.id).first()
if not wl:
    wl = Watchlist(user_id=user.id, name="My Watchlist")
    db.add(wl)
    db.commit()
    db.refresh(wl)
    print("Created watchlist: " + str(wl.id))

for stock in db.query(Stock).all():
    exists = db.query(WatchlistStock).filter_by(watchlist_id=wl.id, stock_id=stock.id).first()
    if not exists:
        db.add(WatchlistStock(watchlist_id=wl.id, stock_id=stock.id))
        print("Added to wl: " + stock.symbol)

db.commit()

sw = db.query(SmartWatchPreference).filter_by(user_id=user.id).first()
if not sw:
    db.add(SmartWatchPreference(user_id=user.id))
    db.commit()
    print("Created SmartWatchPreference")

sess = db.query(UserSession).filter_by(user_id=user.id).first()
if not sess:
    db.add(UserSession(user_id=user.id))
    db.commit()
    print("Created UserSession")

print("Seed complete!")
db.close()
