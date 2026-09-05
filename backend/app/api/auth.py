
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.all_schemas import UserCreate, UserOut, UserGoogleLogin
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
        return {"id": db_user.id, "name": db_user.name, "email": db_user.email, "picture": db_user.picture, "token": "mock_jwt_token"}
    return {"error": "Invalid"}

@router.post("/google", response_model=UserOut)
def google_login(payload: UserGoogleLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == payload.email).first()
    if not db_user:
        db_user = User(
            name=payload.name,
            email=payload.email,
            password_hash="", # not used
            picture=payload.picture
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    elif db_user.picture != payload.picture:
        db_user.picture = payload.picture
        db.commit()
        db.refresh(db_user)
    return db_user
