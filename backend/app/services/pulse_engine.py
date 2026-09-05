from app.models.all_models import PulseScore, PulseExplanation
from sqlalchemy.orm import Session
from sqlalchemy import desc

def severity_rank(severity: str) -> int:
    return {"CRITICAL": 4, "IMPORTANT": 3, "MODERATE": 2, "NORMAL": 1}.get(severity, 0)

class PulseEngine:
    # Global objective market weights (total = 100%)
    # User-specific thresholds are decoupled and evaluated asynchronously via ARQ workers
    WEIGHT_PRICE = 50
    WEIGHT_VOLUME = 35
    WEIGHT_SECTOR = 15

    @classmethod
    def evaluate(cls, db: Session, snapshot, user_threshold=None, **kwargs):
        """
        Evaluates the global, objective market pulse score for a stock snapshot.
        User thresholds are decoupled from this calculation and evaluated
        per-user in the ARQ change detector worker.
        """
        price_change_pct = abs(snapshot.price - snapshot.previous_price) / snapshot.previous_price if snapshot.previous_price else 0.0
        volume_ratio = snapshot.volume / snapshot.average_volume if snapshot.average_volume else 1.0
        sector_rel = abs(price_change_pct - abs(snapshot.sector_change)) if snapshot.sector_change is not None else price_change_pct
        
        price_signal = min(100.0, (price_change_pct / 0.05) * 100.0)
        volume_signal = min(100.0, max(0.0, (volume_ratio - 1.0) / 2.0) * 100.0)
        sector_signal = min(100.0, max(0.0, sector_rel / 0.03) * 100.0)
        threshold_signal = 0.0  # Decoupled to user-specific ARQ workers
        
        final_score_raw = (
            (price_signal * cls.WEIGHT_PRICE) +
            (volume_signal * cls.WEIGHT_VOLUME) +
            (sector_signal * cls.WEIGHT_SECTOR)
        ) / 100.0
        
        final_score = int(max(0, min(100, final_score_raw)))
        
        if final_score <= 30:
            severity = "NORMAL"
        elif final_score <= 60:
            severity = "MODERATE"
        elif final_score <= 80:
            severity = "IMPORTANT"
        else:
            severity = "CRITICAL"
            
        prev_score_record = db.query(PulseScore).filter(PulseScore.stock_id == snapshot.stock_id).order_by(desc(PulseScore.id)).first()
        if prev_score_record:
            momentum = float(final_score - prev_score_record.score)
        else:
            momentum = 0.0
        
        score_record = PulseScore(
            stock_id=snapshot.stock_id,
            score=final_score,
            price_signal=price_signal,
            volume_signal=volume_signal,
            sector_signal=sector_signal,
            threshold_signal=threshold_signal,
            severity=severity,
            momentum=momentum
        )
        db.add(score_record)
        db.commit()
        db.refresh(score_record)
        
        if price_signal > 0:
            exp = PulseExplanation(
                pulse_score_id=score_record.id,
                reason_type="PRICE",
                message=f"Price moved by {price_change_pct*100:.1f}%",
                impact=int(price_signal * cls.WEIGHT_PRICE)
            )
            db.add(exp)
        if volume_signal > 0:
            exp = PulseExplanation(
                pulse_score_id=score_record.id,
                reason_type="VOLUME",
                message=f"Volume is {volume_ratio:.1f}× the average",
                impact=int(volume_signal * cls.WEIGHT_VOLUME)
            )
            db.add(exp)
        if sector_signal > 0:
            exp = PulseExplanation(
                pulse_score_id=score_record.id,
                reason_type="SECTOR",
                message=f"Outperformed sector by {sector_rel*100:.1f}%",
                impact=int(sector_signal * cls.WEIGHT_SECTOR)
            )
            db.add(exp)
            
        db.commit()
        return score_record
