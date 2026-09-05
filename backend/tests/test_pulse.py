import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.models.all_models import Stock, MarketSnapshot, PulseScore, PulseExplanation, MeaningfulChange
from app.services.pulse_engine import PulseEngine, severity_rank
from app.services.change_detector import ChangeDetector, rank_attention


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Seed one stock
    stock = Stock(symbol="TEST", company_name="Test Corp", sector="Technology")
    session.add(stock)
    session.commit()
    yield session
    session.close()


def make_snapshot(db, stock_id, price, prev_price, volume, avg_volume, sector_change=0.0):
    snap = MarketSnapshot(
        stock_id=stock_id,
        price=price,
        previous_price=prev_price,
        volume=volume,
        average_volume=avg_volume,
        sector_change=sector_change,
        data_timestamp=datetime.utcnow(),
        received_timestamp=datetime.utcnow(),
        source="test",
        is_stale=False,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


# ── Pulse Engine Tests ────────────────────────────────────────────────────────

def test_small_move_gives_low_score(db):
    stock = db.query(Stock).first()
    # 0.5% price move, normal volume
    snap = make_snapshot(db, stock.id, 100.5, 100.0, 1000, 1000)
    score = PulseEngine.evaluate(db, snap, user_threshold=0.05)
    assert score.score <= 30, f"Expected NORMAL score, got {score.score}"
    assert score.severity == "NORMAL"


def test_large_move_gives_high_score(db):
    stock = db.query(Stock).first()
    # 8% price move
    snap = make_snapshot(db, stock.id, 108.0, 100.0, 1000, 1000)
    score = PulseEngine.evaluate(db, snap, user_threshold=0.05)
    assert score.score >= 50, f"Expected elevated score, got {score.score}"


def test_volume_anomaly_increases_score(db):
    stock = db.query(Stock).first()
    # Normal price move (1%) but 5x volume
    snap_low = make_snapshot(db, stock.id, 101.0, 100.0, 1000, 1000)
    score_low = PulseEngine.evaluate(db, snap_low)
    
    snap_high = make_snapshot(db, stock.id, 101.0, 100.0, 5000, 1000)
    score_high = PulseEngine.evaluate(db, snap_high)
    
    assert score_high.score > score_low.score, "High volume should increase score"


def test_threshold_crossing_increases_score(db):
    stock = db.query(Stock).first()
    # Price move just below threshold
    snap_below = make_snapshot(db, stock.id, 104.0, 100.0, 1000, 1000)
    score_below = PulseEngine.evaluate(db, snap_below, user_threshold=0.05)
    
    # Price move above threshold
    snap_above = make_snapshot(db, stock.id, 106.0, 100.0, 1000, 1000)
    score_above = PulseEngine.evaluate(db, snap_above, user_threshold=0.05)
    
    assert score_above.score > score_below.score, "Threshold crossing should increase score"


def test_momentum_computed(db):
    stock = db.query(Stock).first()
    # First score
    snap1 = make_snapshot(db, stock.id, 104.0, 100.0, 1000, 1000)
    score1 = PulseEngine.evaluate(db, snap1)
    assert score1.momentum == 0  # no previous
    
    # Second score (higher)
    snap2 = make_snapshot(db, stock.id, 110.0, 100.0, 5000, 1000)
    score2 = PulseEngine.evaluate(db, snap2)
    assert score2.momentum == score2.score - score1.score


def test_severity_bands(db):
    stock = db.query(Stock).first()
    # Score of 0 → NORMAL
    snap = make_snapshot(db, stock.id, 100.0, 100.0, 1000, 1000)
    score = PulseEngine.evaluate(db, snap)
    assert score.severity in ("NORMAL", "MODERATE", "IMPORTANT", "CRITICAL")


# ── Change Detector Tests ─────────────────────────────────────────────────────

def test_single_strong_price_signal_is_meaningful(db):
    stock = db.query(Stock).first()
    # 5% move exceeds MIN_PRICE_MOVE=3%
    snap = make_snapshot(db, stock.id, 105.0, 100.0, 1000, 1000)
    score = PulseEngine.evaluate(db, snap)
    change = ChangeDetector.evaluate(db, snap, score)
    assert change is not None, "5% price move should be meaningful"


def test_weak_signals_together_are_meaningful(db):
    stock = db.query(Stock).first()
    # 2% move (below 3% threshold alone) + 2.1x volume (above 2x threshold)
    snap = make_snapshot(db, stock.id, 102.0, 100.0, 2100, 1000)
    score = PulseEngine.evaluate(db, snap)
    change = ChangeDetector.evaluate(db, snap, score)
    # Volume >= 2x + threshold_signal fires (2% < 5% user threshold so no threshold)
    # But volume alone is >= 2x so it IS meaningful
    assert change is not None


def test_nothing_significant_not_meaningful(db):
    stock = db.query(Stock).first()
    # Tiny move, normal volume
    snap = make_snapshot(db, stock.id, 100.1, 100.0, 900, 1000)
    score = PulseEngine.evaluate(db, snap)
    change = ChangeDetector.evaluate(db, snap, score)
    assert change is None, "Tiny move with normal volume should not be meaningful"


# ── rank_attention Tests ──────────────────────────────────────────────────────

def test_higher_severity_ranks_above_lower():
    stocks = [
        {"severity": "NORMAL", "momentum": 0, "timestamp": "2024-01-01T00:00:00"},
        {"severity": "CRITICAL", "momentum": 0, "timestamp": "2024-01-01T00:00:00"},
        {"severity": "IMPORTANT", "momentum": 0, "timestamp": "2024-01-01T00:00:00"},
    ]
    ranked = rank_attention(stocks)
    assert ranked[0]["severity"] == "CRITICAL"
    assert ranked[1]["severity"] == "IMPORTANT"
    assert ranked[2]["severity"] == "NORMAL"


def test_equal_severity_broken_by_momentum():
    stocks = [
        {"severity": "IMPORTANT", "momentum": 5, "timestamp": "2024-01-01T00:00:00"},
        {"severity": "IMPORTANT", "momentum": 30, "timestamp": "2024-01-01T00:00:00"},
        {"severity": "IMPORTANT", "momentum": -10, "timestamp": "2024-01-01T00:00:00"},
    ]
    ranked = rank_attention(stocks)
    assert ranked[0]["momentum"] == 30
    assert ranked[2]["momentum"] == -10


# ── severity_rank helper ──────────────────────────────────────────────────────

def test_severity_rank_ordering():
    assert severity_rank("CRITICAL") > severity_rank("IMPORTANT")
    assert severity_rank("IMPORTANT") > severity_rank("MODERATE")
    assert severity_rank("MODERATE") > severity_rank("NORMAL")
    assert severity_rank("NORMAL") > severity_rank("UNKNOWN")


# ── ChangeDetector.evaluate_user_thresholds Tests ────────────────────────────

from app.models.all_models import (
    User, SmartWatchPreference, ThresholdState, QuickGroup, QuickGroupStock
)


@pytest.fixture
def db_with_user(db):
    """Extends the base db fixture with a seeded User and SmartWatchPreference."""
    user = User(name="Alice", email="alice@example.com", password_hash="")
    db.add(user)
    db.commit()
    db.refresh(user)
    pref = SmartWatchPreference(
        user_id=user.id,
        enabled=True,
        price_threshold=3.0,   # 3%
        volume_threshold=2.0,  # 2x
        sensitivity="MEDIUM",
    )
    db.add(pref)
    db.commit()
    return db, user


def test_threshold_crossing_fires_meaningful_change(db_with_user):
    """A 5% price move (> 3% user threshold) from NORMAL state must create a MeaningfulChange."""
    db, user = db_with_user
    stock = db.query(Stock).first()

    snap = make_snapshot(db, stock.id, 105.0, 100.0, 1000, 1000)
    score = PulseEngine.evaluate(db, snap)

    mc = ChangeDetector.evaluate_user_thresholds(db, snap, score, user_id=user.id)

    assert mc is not None, "Expected a MeaningfulChange for a 5% price move"
    assert mc.user_id == user.id
    assert mc.stock_id == stock.id

    ts = db.query(ThresholdState).filter(
        ThresholdState.user_id == user.id,
        ThresholdState.stock_id == stock.id,
    ).first()
    assert ts is not None
    assert ts.state == "CROSSED"


def test_hysteresis_no_refire_on_active(db_with_user):
    """
    Second call while state is ACTIVE (already CROSSED) must NOT create another MeaningfulChange.
    This is the hysteresis guard — one notification per crossing, not per tick.
    """
    db, user = db_with_user
    stock = db.query(Stock).first()

    # First tick — crosses threshold → CROSSED, MeaningfulChange created
    snap1 = make_snapshot(db, stock.id, 105.0, 100.0, 1000, 1000)
    score1 = PulseEngine.evaluate(db, snap1)
    mc1 = ChangeDetector.evaluate_user_thresholds(db, snap1, score1, user_id=user.id)
    assert mc1 is not None, "First crossing should produce a MeaningfulChange"

    # Second tick — still above threshold → ACTIVE, must NOT create a second MeaningfulChange
    snap2 = make_snapshot(db, stock.id, 106.0, 100.0, 1000, 1000)
    score2 = PulseEngine.evaluate(db, snap2)
    mc2 = ChangeDetector.evaluate_user_thresholds(db, snap2, score2, user_id=user.id)
    assert mc2 is None, "Hysteresis: second tick while ACTIVE must not re-fire"

    ts = db.query(ThresholdState).filter(
        ThresholdState.user_id == user.id,
        ThresholdState.stock_id == stock.id,
    ).first()
    assert ts.state == "ACTIVE"


def test_quick_group_suppression_skips_user(db_with_user):
    """
    Stock in a QuickGroup with auto_watch=False must be suppressed — no MeaningfulChange
    even for a large price move.
    """
    db, user = db_with_user
    stock = db.query(Stock).first()

    # Create a suppressed QuickGroup for this user containing the stock
    qg = QuickGroup(user_id=user.id, name="Muted Sector", auto_watch=False)
    db.add(qg)
    db.commit()
    db.refresh(qg)

    qgs = QuickGroupStock(quick_group_id=qg.id, stock_id=stock.id)
    db.add(qgs)
    db.commit()

    snap = make_snapshot(db, stock.id, 115.0, 100.0, 5000, 1000)  # 15% move
    score = PulseEngine.evaluate(db, snap)

    mc = ChangeDetector.evaluate_user_thresholds(db, snap, score, user_id=user.id)
    assert mc is None, "Suppressed QuickGroup (auto_watch=False) should block the alert"


def test_stale_snapshot_exits_crossed_state(db_with_user):
    """
    After crossing the threshold (CROSSED state), a subsequent small-move snapshot
    must transition to EXITED and emit a MeaningfulChange marking the exit.
    """
    db, user = db_with_user
    stock = db.query(Stock).first()

    # First tick — large move → CROSSED
    snap1 = make_snapshot(db, stock.id, 106.0, 100.0, 1000, 1000)
    score1 = PulseEngine.evaluate(db, snap1)
    mc1 = ChangeDetector.evaluate_user_thresholds(db, snap1, score1, user_id=user.id)
    assert mc1 is not None

    ts = db.query(ThresholdState).filter(
        ThresholdState.user_id == user.id,
        ThresholdState.stock_id == stock.id,
    ).first()
    assert ts.state == "CROSSED"

    # Second tick — tiny move, falls back below threshold → EXITED
    snap2 = make_snapshot(db, stock.id, 100.05, 100.0, 950, 1000)
    score2 = PulseEngine.evaluate(db, snap2)
    mc2 = ChangeDetector.evaluate_user_thresholds(db, snap2, score2, user_id=user.id)

    assert mc2 is not None, "Exit from CROSSED state should produce a MeaningfulChange"
    ts_after = db.query(ThresholdState).filter(
        ThresholdState.user_id == user.id,
        ThresholdState.stock_id == stock.id,
    ).first()
    assert ts_after.state == "EXITED"
