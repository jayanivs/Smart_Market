import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse\backend\app\services"

files = {
    "__init__.py": "",
    "preference_resolver.py": """
from sqlalchemy.orm import Session
from app.models.all_models import SmartWatchPreference, Category

def resolve_preferences(db: Session, user_id: int, category_id: int = None) -> SmartWatchPreference:
    # Get global defaults if no specific preference
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id, 
        SmartWatchPreference.category_id == category_id
    ).first()
    
    if prefs:
        return prefs
        
    if category_id:
        # Check parent
        cat = db.query(Category).filter(Category.id == category_id).first()
        if cat and cat.parent_id:
            return resolve_preferences(db, user_id, cat.parent_id)
            
    # Finally return global
    global_prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id, 
        SmartWatchPreference.category_id == None
    ).first()
    
    if global_prefs:
        return global_prefs
        
    return SmartWatchPreference(enabled=True, price_threshold=5.0, volume_threshold=2.0)
""",
    "pulse_engine.py": """
from app.models.all_models import MarketSnapshot, PulseScore, PulseExplanation
from sqlalchemy.orm import Session
from .preference_resolver import resolve_preferences

def calculate_pulse(db: Session, user_id: int, current_snap: MarketSnapshot, previous_snap: MarketSnapshot, category_id: int = None):
    prefs = resolve_preferences(db, user_id, category_id)
    
    if not previous_snap:
        # No history, default to 0
        return 0, [], "NORMAL"
        
    # Signals
    price_change_pct = ((current_snap.price - previous_snap.price) / previous_snap.price) * 100 if previous_snap.price else 0
    price_signal = min(abs(price_change_pct) * 6, 30) # max 30
    
    volume_ratio = current_snap.volume / (current_snap.average_volume or 1)
    volume_signal = min((volume_ratio - 1) * 12.5, 25) if volume_ratio > 1 else 0 # max 25

    sector_diff = price_change_pct - current_snap.sector_change
    sector_signal = min(abs(sector_diff) * 5, 25) # max 25
    
    threshold_signal = 20 if abs(price_change_pct) >= prefs.price_threshold else 0
    
    score = price_signal + volume_signal + sector_signal + threshold_signal
    score = min(max(int(score), 0), 100)
    
    if score >= 81:
        severity = "CRITICAL"
    elif score >= 61:
        severity = "IMPORTANT"
    elif score >= 31:
        severity = "MODERATE"
    else:
        severity = "NORMAL"
        
    reasons = []
    if price_signal > 0:
        reasons.append({"type": "PRICE", "message": f"Price {'increased' if price_change_pct > 0 else 'decreased'} by {abs(price_change_pct):.1f}%", "impact": int(price_signal)})
    if volume_signal > 0:
        reasons.append({"type": "VOLUME", "message": f"Volume is {volume_ratio:.1f}x above normal", "impact": int(volume_signal)})
    if sector_signal > 0:
        reasons.append({"type": "SECTOR", "message": f"{'Outperformed' if sector_diff > 0 else 'Underperformed'} sector by {abs(sector_diff):.1f}%", "impact": int(sector_signal)})
    if threshold_signal > 0:
        reasons.append({"type": "THRESHOLD", "message": f"Your {prefs.price_threshold}% threshold was crossed", "impact": int(threshold_signal)})
        
    return score, reasons, severity
""",
    "change_detector.py": """
def is_meaningful_change(previous_score: int, current_score: int, severity: str) -> bool:
    if severity in ["CRITICAL", "IMPORTANT"]:
        if current_score - previous_score >= 15:
            return True
        if current_score > 80:
            return True
    return False
""",
    "market_data.py": """
from app.models.all_models import MarketSnapshot
from datetime import datetime

class MarketDataService:
    @staticmethod
    def create_snapshot(symbol: str, price: float, previous_price: float, volume: int, avg_volume: int, sector_change: float) -> MarketSnapshot:
        return MarketSnapshot(
            price=price,
            previous_price=previous_price,
            volume=volume,
            average_volume=avg_volume,
            sector_change=sector_change,
            timestamp=datetime.utcnow(),
            source="market_api",
            data_timestamp=datetime.utcnow(),
            received_timestamp=datetime.utcnow(),
            is_stale=False
        )
""",
    "websocket_manager.py": """
from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
"""
}

for filepath, content in files.items():
    full_path = os.path.join(BASE_DIR, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Services created.")
