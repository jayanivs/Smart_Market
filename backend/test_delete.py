import sys
from app.database.database import SessionLocal
from app.models.all_models import Watchlist, WatchlistStock

db = SessionLocal()
# Create a dummy watchlist
wl = Watchlist(user_id=1, name="Test")
db.add(wl)
db.commit()
db.refresh(wl)

print("Created watchlist", wl.id)

# Try deleting like the endpoint
try:
    db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).delete()
    db.delete(wl)
    db.commit()
    print("Deleted successfully")
except Exception as e:
    print("Error:", type(e).__name__, e)
