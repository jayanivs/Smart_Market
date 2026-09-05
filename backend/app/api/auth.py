import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.all_models import User
from app.schemas.all_schemas import UserCreate, UserOut, UserGoogleLogin

router = APIRouter()

# ── JWT configuration ────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days default


def create_access_token(user_id: int, email: str) -> str:
    """Issue a signed JWT containing user_id and email."""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_response(user: User) -> dict:
    """Build the standard auth response including a fresh JWT."""
    token = create_access_token(user.id, user.email)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "token": token,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=user.password,  # mock plain — replace with bcrypt in prod
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return _user_response(db_user)


@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _user_response(db_user)


@router.post("/google")
def google_login(payload: UserGoogleLogin, db: Session = Depends(get_db)):
    """
    Upsert user from Google OAuth payload and return a signed JWT.
    The frontend must store the token and send it as:
        Authorization: Bearer <token>
    on all subsequent requests.
    """
    db_user = db.query(User).filter(User.email == payload.email).first()
    if not db_user:
        db_user = User(
            name=payload.name,
            email=payload.email,
            password_hash="",  # not used for OAuth users
            picture=payload.picture,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    elif db_user.picture != payload.picture:
        db_user.picture = payload.picture
        db.commit()
        db.refresh(db_user)

    return _user_response(db_user)
