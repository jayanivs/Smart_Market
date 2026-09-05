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
    picture = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    company_name = Column(String)
    sector = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    stocks = relationship("WatchlistStock", backref="watchlist", lazy="dynamic")

class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    price = Column(Float)
    previous_price = Column(Float)
    volume = Column(Integer)
    average_volume = Column(Integer)
    sector_change = Column(Float)
    data_timestamp = Column(DateTime, index=True)
    received_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String)
    is_stale = Column(Boolean, default=False)

class PulseScore(Base):
    __tablename__ = "pulse_scores"
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    score = Column(Integer)
    price_signal = Column(Float)
    volume_signal = Column(Float)
    sector_signal = Column(Float)
    threshold_signal = Column(Float)
    momentum = Column(Float, default=0.0)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    explanations = relationship("PulseExplanation", backref="pulse_score", lazy="select")

class PulseExplanation(Base):
    __tablename__ = "pulse_explanations"
    id = Column(Integer, primary_key=True, index=True)
    pulse_score_id = Column(Integer, ForeignKey("pulse_scores.id"), index=True)
    reason_type = Column(String)
    message = Column(Text)
    impact = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class MeaningfulChange(Base):
    __tablename__ = "meaningful_changes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    pulse_score_id = Column(Integer, ForeignKey("pulse_scores.id"))
    previous_score = Column(Integer)
    current_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    seen_at = Column(DateTime, nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    last_visit_at = Column(DateTime, default=datetime.utcnow)

class SmartWatchPreference(Base):
    __tablename__ = "smart_watch_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    enabled = Column(Boolean, default=True)
    price_threshold = Column(Float, default=5.0)  # percent, e.g. 5.0 = 5%
    volume_threshold = Column(Float, default=2.0)  # ratio, e.g. 2.0 = 2x average
    sensitivity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuickGroup(Base):
    __tablename__ = "quick_groups"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String)
    sensitivity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH
    auto_watch = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    stocks = relationship("QuickGroupStock", backref="quick_group", cascade="all, delete-orphan")

class QuickGroupStock(Base):
    __tablename__ = "quick_group_stocks"
    id = Column(Integer, primary_key=True, index=True)
    quick_group_id = Column(Integer, ForeignKey("quick_groups.id"), index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)

class ThresholdState(Base):
    __tablename__ = "threshold_states"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    state = Column(String, default="NORMAL")  # NORMAL, CROSSED, ACTIVE, EXITED
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

