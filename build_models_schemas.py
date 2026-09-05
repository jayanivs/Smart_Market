import os

BASE_DIR = r"c:\Users\sithi\OneDrive\Desktop\GROW\market-pulse\backend\app"

models_code = """
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    company_name = Column(String)
    sector = Column(String)
    industry = Column(String)
    ownership_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SmartWatchPreference(Base):
    __tablename__ = "smart_watch_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    enabled = Column(Boolean, default=True)
    price_threshold = Column(Float, default=5.0)
    volume_threshold = Column(Float, default=2.0)
    sensitivity = Column(String, default="MEDIUM")
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    price = Column(Float)
    previous_price = Column(Float)
    volume = Column(Integer)
    average_volume = Column(Integer)
    sector_change = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String)
    data_timestamp = Column(DateTime)
    received_timestamp = Column(DateTime, default=datetime.utcnow)
    is_stale = Column(Boolean, default=False)

class PulseScore(Base):
    __tablename__ = "pulse_scores"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    score = Column(Integer)
    price_signal = Column(Float)
    volume_signal = Column(Float)
    sector_signal = Column(Float)
    threshold_signal = Column(Float)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PulseExplanation(Base):
    __tablename__ = "pulse_explanations"
    id = Column(Integer, primary_key=True, index=True)
    pulse_score_id = Column(Integer, ForeignKey("pulse_scores.id"))
    reason_type = Column(String)
    message = Column(Text)
    impact = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    type = Column(String)
    severity = Column(String)
    title = Column(String)
    message = Column(Text)
    pulse_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    last_visit_at = Column(DateTime, default=datetime.utcnow)

class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    week_start = Column(DateTime)
    week_end = Column(DateTime)
    total_changes = Column(Integer, default=0)
    critical_changes = Column(Integer, default=0)
    important_changes = Column(Integer, default=0)
    top_stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True)
    top_sector = Column(String)
    threshold_crossings = Column(Integer, default=0)
    volume_anomalies = Column(Integer, default=0)
    generated_at = Column(DateTime, default=datetime.utcnow)
"""

schemas_code = """
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True

class StockOut(BaseModel):
    id: int
    symbol: str
    company_name: str
    sector: str
    industry: str
    class Config:
        orm_mode = True

class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    class Config:
        orm_mode = True

class WatchlistCreate(BaseModel):
    name: str

class WatchlistOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class PulseExplanationOut(BaseModel):
    type: str
    message: str
    impact: int
    class Config:
        orm_mode = True

class PulseResult(BaseModel):
    score: int
    severity: str
    reasons: List[PulseExplanationOut] = []

class NotificationOut(BaseModel):
    id: int
    stock_id: int
    type: str
    severity: str
    title: str
    message: str
    created_at: datetime
    read_at: Optional[datetime] = None
    class Config:
        orm_mode = True
"""

os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)
with open(os.path.join(BASE_DIR, "models", "all_models.py"), "w", encoding="utf-8") as f:
    f.write(models_code)

with open(os.path.join(BASE_DIR, "models", "__init__.py"), "w", encoding="utf-8") as f:
    f.write("from .all_models import *\n")

os.makedirs(os.path.join(BASE_DIR, "schemas"), exist_ok=True)
with open(os.path.join(BASE_DIR, "schemas", "all_schemas.py"), "w", encoding="utf-8") as f:
    f.write(schemas_code)

with open(os.path.join(BASE_DIR, "schemas", "__init__.py"), "w", encoding="utf-8") as f:
    f.write("from .all_schemas import *\n")

print("Models and Schemas created.")
