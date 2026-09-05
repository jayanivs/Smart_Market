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

class UserGoogleLogin(BaseModel):
    name: str
    email: str
    picture: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    picture: Optional[str] = None
    class Config:
        from_attributes = True

class StockOut(BaseModel):
    id: int
    symbol: str
    company_name: str
    sector: str
    class Config:
        from_attributes = True

class WatchlistCreate(BaseModel):
    name: str

class WatchlistOut(BaseModel):
    id: int
    name: str
    stocks: List[StockOut] = []
    class Config:
        from_attributes = True

class WatchlistAddStock(BaseModel):
    stock_id: int

class PulseExplanationOut(BaseModel):
    id: int
    reason_type: str
    message: str
    impact: int
    class Config:
        from_attributes = True

class SnapshotInfo(BaseModel):
    price: Optional[float] = None
    previous_price: Optional[float] = None
    volume: Optional[int] = None
    average_volume: Optional[int] = None
    is_stale: Optional[bool] = False
    data_timestamp: Optional[datetime] = None
    class Config:
        from_attributes = True

class PulseScoreOut(BaseModel):
    id: int
    stock_id: int
    score: int
    price_signal: float
    volume_signal: float
    sector_signal: float
    threshold_signal: float
    severity: str
    momentum: float = 0.0
    timestamp: datetime
    explanations: List[PulseExplanationOut] = []
    stock: Optional[StockOut] = None
    snapshot: Optional[SnapshotInfo] = None
    class Config:
        from_attributes = True

class MeaningfulChangeOut(BaseModel):
    id: int
    stock_id: int
    previous_score: int
    current_score: int
    created_at: datetime
    seen_at: Optional[datetime] = None
    stock: Optional[StockOut] = None
    pulse_score_id: Optional[int] = None
    class Config:
        from_attributes = True

class MarketChangeSimulate(BaseModel):
    stock_id: int
    current_price: float
    previous_price: float
    volume: int
    avg_volume: int
    sector_change: float

class SmartWatchPreferenceOut(BaseModel):
    id: int
    user_id: int
    enabled: bool
    price_threshold: float
    volume_threshold: float
    sensitivity: str
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class SmartWatchPreferenceUpdate(BaseModel):
    price_threshold: Optional[float] = None
    volume_threshold: Optional[float] = None
    sensitivity: Optional[str] = None

class NotificationOut(BaseModel):
    id: int
    stock_id: int
    stock: Optional[StockOut] = None
    previous_score: int
    current_score: int
    severity: str
    message: str
    created_at: datetime
    seen_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class QuickGroupCreate(BaseModel):
    name: str = ""
    stock_ids: List[int] = []
    sensitivity: str = "MEDIUM"
    auto_watch: bool = False

class QuickGroupUpdate(BaseModel):
    sensitivity: Optional[str] = None
    auto_watch: Optional[bool] = None

