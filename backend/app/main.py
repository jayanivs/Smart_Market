from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base, SessionLocal
from app.api import api_router
from app.api.websockets import ws_router

# Create all DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MARKET PULSE", description="A watchlist that watches for you.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


import asyncio

@app.on_event("startup")
async def startup_event():
    """Seed the database with demo data on first run, then start live data polling."""
    from app.database.seed import seed_database
    from app.services.market_data import MarketDataService
    from app.services.websocket_manager import manager
    await manager.init_redis()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    # Background task: fetch live NSE data every 5 minutes
    async def live_poll_loop():
        while True:
            await asyncio.sleep(300)  # 5 minutes
            db2 = SessionLocal()
            try:
                MarketDataService.run_yfinance_fetcher(db2, user_threshold=5.0)
            except Exception as e:
                print(f"[LivePoll] Error fetching live data: {e}")
            finally:
                db2.close()

    asyncio.create_task(live_poll_loop())


@app.get("/")
def root():
    return {"message": "Market Pulse API is running. Visit /docs for the API reference."}
