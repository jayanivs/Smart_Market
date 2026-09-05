from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.all_models import Stock
from app.schemas.all_schemas import StockOut
from typing import List

router = APIRouter()

@router.get("", response_model=List[StockOut])
def get_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    return stocks
