import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse\backend\app"

main_code = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.api import api_router
from app.api.websockets import ws_router

# Create DB Tables
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

@app.get("/")
def root():
    return {"message": "Market Pulse API is running."}
"""

api_init = """
from fastapi import APIRouter
from .auth import router as auth_router
from .simulator import router as sim_router
from .stocks import router as stock_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sim_router, prefix="/simulator", tags=["simulator"])
api_router.include_router(stock_router, prefix="/stocks", tags=["stocks"])
# Other routers would be added here
"""

auth_api = """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.all_schemas import UserCreate, UserOut
from app.models.all_models import User

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email, password_hash=user.password) # mock plain for hackathon
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        return {"id": db_user.id, "name": db_user.name, "token": "mock_jwt_token"}
    return {"error": "Invalid"}
"""

simulator_api = """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.market_data import MarketDataService
from app.services.pulse_engine import calculate_pulse
from app.services.change_detector import is_meaningful_change
from app.services.websocket_manager import manager
from app.models.all_models import Stock, PulseScore, PulseExplanation
from pydantic import BaseModel
import asyncio

router = APIRouter()

class SimRequest(BaseModel):
    stock_id: int
    user_id: int
    current_price: float
    previous_price: float
    volume: int
    avg_volume: int
    sector_change: float

@router.post("/market-change")
async def simulate_market_change(req: SimRequest, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == req.stock_id).first()
    if not stock:
        # Mock stock creation
        stock = Stock(id=req.stock_id, symbol="INFY", company_name="Infosys", sector="IT", industry="IT")
        db.add(stock)
        db.commit()
        db.refresh(stock)
        
    current_snap = MarketDataService.create_snapshot(
        symbol=stock.symbol, price=req.current_price, previous_price=req.previous_price,
        volume=req.volume, avg_volume=req.avg_volume, sector_change=req.sector_change
    )
    current_snap.stock_id = stock.id
    
    prev_snap = MarketDataService.create_snapshot(
        symbol=stock.symbol, price=req.previous_price, previous_price=req.previous_price,
        volume=req.avg_volume, avg_volume=req.avg_volume, sector_change=0
    )
    
    score, reasons, severity = calculate_pulse(db, req.user_id, current_snap, prev_snap)
    
    db_pulse = PulseScore(
        stock_id=stock.id, score=score, severity=severity,
        price_signal=score, # Simplified storage
        volume_signal=0, sector_signal=0, threshold_signal=0
    )
    db.add(db_pulse)
    db.commit()
    db.refresh(db_pulse)
    
    for r in reasons:
        exp = PulseExplanation(pulse_score_id=db_pulse.id, reason_type=r["type"], message=r["message"], impact=r["impact"])
        db.add(exp)
        
    db.commit()

    # Meaningful change
    is_meaningful = is_meaningful_change(0, score, severity) # mock prev 0
    
    # Broadcast
    await manager.broadcast({
        "event": "PULSE_UPDATE",
        "stock": stock.symbol,
        "current_score": score,
        "severity": severity
    })
    
    if is_meaningful:
        await manager.broadcast({
            "event": "NOTIFICATION",
            "stock": stock.symbol,
            "severity": severity,
            "title": f"{stock.symbol} deserves your attention",
            "message": f"Pulse increased to {score}"
        })
        
    return {"message": "Simulated successfully"}
"""

stocks_api = """
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.all_models import Stock
from app.schemas.all_schemas import StockOut

router = APIRouter()

@router.get("/", response_model=list[StockOut])
def get_stocks(db: Session = Depends(get_db)):
    # Initialize some mock data if empty
    if db.query(Stock).count() == 0:
        db.add_all([
            Stock(symbol="INFY", company_name="Infosys", sector="IT", industry="IT", ownership_type="Private"),
            Stock(symbol="TCS", company_name="Tata Consultancy Services", sector="IT", industry="IT", ownership_type="Private"),
            Stock(symbol="HDFCBANK", company_name="HDFC Bank", sector="Financial", industry="Banking", ownership_type="Private"),
            Stock(symbol="SBI", company_name="State Bank of India", sector="Financial", industry="Banking", ownership_type="Government")
        ])
        db.commit()
    return db.query(Stock).all()
"""

ws_api = """
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager

ws_router = APIRouter()

@ws_router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
"""

os.makedirs(os.path.join(BASE_DIR, "api"), exist_ok=True)
with open(os.path.join(BASE_DIR, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_code)
with open(os.path.join(BASE_DIR, "api", "__init__.py"), "w", encoding="utf-8") as f:
    f.write(api_init)
with open(os.path.join(BASE_DIR, "api", "auth.py"), "w", encoding="utf-8") as f:
    f.write(auth_api)
with open(os.path.join(BASE_DIR, "api", "simulator.py"), "w", encoding="utf-8") as f:
    f.write(simulator_api)
with open(os.path.join(BASE_DIR, "api", "stocks.py"), "w", encoding="utf-8") as f:
    f.write(stocks_api)
with open(os.path.join(BASE_DIR, "api", "websockets.py"), "w", encoding="utf-8") as f:
    f.write(ws_api)

print("API layer created.")
