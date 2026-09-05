from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database.connection import get_db
from app.models.all_models import SmartWatchPreference
from app.schemas.all_schemas import SmartWatchPreferenceOut, SmartWatchPreferenceUpdate
from app.api.deps import get_current_user_id

router = APIRouter()


@router.get("", response_model=SmartWatchPreferenceOut)
def get_smart_watch(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id
    ).first()
    if not prefs:
        # Create default on first access
        prefs = SmartWatchPreference(
            user_id=user_id,
            enabled=True,
            price_threshold=5.0,
            volume_threshold=2.0,
            sensitivity="MEDIUM",
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.patch("", response_model=SmartWatchPreferenceOut)
def update_smart_watch(update: SmartWatchPreferenceUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id
    ).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found. Call GET first.")

    if update.price_threshold is not None:
        prefs.price_threshold = update.price_threshold
    if update.volume_threshold is not None:
        prefs.volume_threshold = update.volume_threshold
    if update.sensitivity is not None:
        valid_sensitivities = {"LOW", "MEDIUM", "HIGH"}
        if update.sensitivity not in valid_sensitivities:
            raise HTTPException(status_code=422, detail=f"sensitivity must be one of {valid_sensitivities}")
        prefs.sensitivity = update.sensitivity
        # Apply preset thresholds for sensitivity levels
        presets = {
            "LOW":    {"price_threshold": 8.0, "volume_threshold": 3.0},
            "MEDIUM": {"price_threshold": 5.0, "volume_threshold": 2.0},
            "HIGH":   {"price_threshold": 2.0, "volume_threshold": 1.5},
        }
        preset = presets[update.sensitivity]
        if update.price_threshold is None:
            prefs.price_threshold = preset["price_threshold"]
        if update.volume_threshold is None:
            prefs.volume_threshold = preset["volume_threshold"]

    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.post("/toggle", response_model=SmartWatchPreferenceOut)
def toggle_smart_watch(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    prefs = db.query(SmartWatchPreference).filter(
        SmartWatchPreference.user_id == user_id
    ).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found. Call GET first.")
    prefs.enabled = not prefs.enabled
    prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs
