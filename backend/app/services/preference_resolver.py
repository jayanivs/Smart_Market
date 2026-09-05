
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
