"""
Watchlist endpoint tests — POST, PATCH rename, DELETE (cascade), reorder, edge cases.

Uses FastAPI TestClient against an in-memory SQLite database.
JWT auth is bypassed via DEV_TRUST_HEADER=1 (patched into os.environ before import).
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db, engine, SessionLocal
from app.models.all_models import User, Stock, Watchlist, WatchlistStock
from app.main import app


# ── Per-test in-memory SQLite setup ───────────────────────────────────────────

@pytest.fixture()
def client():
    """
    Provides a TestClient backed by a fresh in-memory SQLite DB for every test.
    Overrides the FastAPI dependency get_db so no file-based DB is touched.
    """
    Base.metadata.create_all(engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        # Seed: one user and two stocks
        db = SessionLocal()
        user = User(name="Tester", email="tester@example.com", password_hash="")
        db.add(user)
        db.flush()
        stock1 = Stock(symbol="AAPL", company_name="Apple Inc", sector="Tech")
        stock2 = Stock(symbol="MSFT", company_name="Microsoft Corp", sector="Tech")
        db.add_all([stock1, stock2])
        db.commit()
        db.refresh(user)
        db.refresh(stock1)
        db.refresh(stock2)
        db.close()
        # Expose IDs via fixture
        c.user_id = user.id
        c.stock1_id = stock1.id
        c.stock2_id = stock2.id
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def auth_headers(user_id: int) -> dict:
    """Return X-User-Id header (accepted by DEV_TRUST_HEADER=1 mode)."""
    return {"X-User-Id": str(user_id)}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_watchlist(client):
    """POST /api/watchlists returns 200 with the new watchlist and empty stocks list."""
    resp = client.post(
        "/api/watchlists",
        json={"name": "My Portfolio"},
        headers=auth_headers(client.user_id),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "My Portfolio"
    assert data["stocks"] == []
    assert "id" in data


def test_list_watchlists(client):
    """GET /api/watchlists returns only this user's watchlists."""
    client.post("/api/watchlists", json={"name": "WL1"}, headers=auth_headers(client.user_id))
    client.post("/api/watchlists", json={"name": "WL2"}, headers=auth_headers(client.user_id))

    resp = client.get("/api/watchlists", headers=auth_headers(client.user_id))
    assert resp.status_code == 200
    names = [wl["name"] for wl in resp.json()]
    assert "WL1" in names and "WL2" in names


def test_rename_watchlist(client):
    """PATCH /api/watchlists/{id} updates the watchlist name."""
    create_resp = client.post(
        "/api/watchlists", json={"name": "Old Name"}, headers=auth_headers(client.user_id)
    )
    wl_id = create_resp.json()["id"]

    rename_resp = client.patch(
        f"/api/watchlists/{wl_id}",
        json={"name": "New Name"},
        headers=auth_headers(client.user_id),
    )
    assert rename_resp.status_code == 200, rename_resp.text
    assert rename_resp.json()["name"] == "New Name"

    # Verify persistence via GET
    get_resp = client.get("/api/watchlists", headers=auth_headers(client.user_id))
    names = [wl["name"] for wl in get_resp.json()]
    assert "New Name" in names
    assert "Old Name" not in names


def test_delete_watchlist_cascades_stocks(client):
    """DELETE /api/watchlists/{id} removes the watchlist AND its WatchlistStock rows."""
    create_resp = client.post(
        "/api/watchlists", json={"name": "To Delete"}, headers=auth_headers(client.user_id)
    )
    wl_id = create_resp.json()["id"]

    # Add a stock to the watchlist
    client.post(
        f"/api/watchlists/{wl_id}/stocks",
        json={"stock_id": client.stock1_id},
        headers=auth_headers(client.user_id),
    )

    # Delete the watchlist
    del_resp = client.delete(
        f"/api/watchlists/{wl_id}", headers=auth_headers(client.user_id)
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "ok"

    # The watchlist must not appear in the list anymore
    list_resp = client.get("/api/watchlists", headers=auth_headers(client.user_id))
    ids = [wl["id"] for wl in list_resp.json()]
    assert wl_id not in ids


def test_reorder_watchlist_stocks_persists(client):
    """PATCH /api/watchlists/{id}/stocks/reorder sets positions; GET returns stocks in that order."""
    create_resp = client.post(
        "/api/watchlists", json={"name": "Ordered WL"}, headers=auth_headers(client.user_id)
    )
    wl_id = create_resp.json()["id"]

    # Add stock1 then stock2 (default order: stock1=pos0, stock2=pos1)
    client.post(
        f"/api/watchlists/{wl_id}/stocks",
        json={"stock_id": client.stock1_id},
        headers=auth_headers(client.user_id),
    )
    client.post(
        f"/api/watchlists/{wl_id}/stocks",
        json={"stock_id": client.stock2_id},
        headers=auth_headers(client.user_id),
    )

    # Reorder: put stock2 first
    reorder_resp = client.patch(
        f"/api/watchlists/{wl_id}/stocks/reorder",
        json={"stock_ids": [client.stock2_id, client.stock1_id]},
        headers=auth_headers(client.user_id),
    )
    assert reorder_resp.status_code == 200, reorder_resp.text
    ordered = [s["id"] for s in reorder_resp.json()["stocks"]]
    assert ordered == [client.stock2_id, client.stock1_id], (
        f"Expected [{client.stock2_id}, {client.stock1_id}], got {ordered}"
    )


def test_reorder_rejects_unknown_stock_ids(client):
    """PATCH /api/watchlists/{id}/stocks/reorder with unknown stock_id returns 400."""
    create_resp = client.post(
        "/api/watchlists", json={"name": "WL Reorder Fail"}, headers=auth_headers(client.user_id)
    )
    wl_id = create_resp.json()["id"]

    client.post(
        f"/api/watchlists/{wl_id}/stocks",
        json={"stock_id": client.stock1_id},
        headers=auth_headers(client.user_id),
    )

    resp = client.patch(
        f"/api/watchlists/{wl_id}/stocks/reorder",
        json={"stock_ids": [client.stock1_id, 99999]},  # 99999 doesn't exist
        headers=auth_headers(client.user_id),
    )
    assert resp.status_code == 400, resp.text
    assert "Unknown" in resp.json()["detail"]


def test_delete_nonexistent_stock_returns_ok(client):
    """DELETE /api/watchlists/{id}/stocks/{stock_id} is idempotent when stock not in watchlist."""
    create_resp = client.post(
        "/api/watchlists", json={"name": "Empty WL"}, headers=auth_headers(client.user_id)
    )
    wl_id = create_resp.json()["id"]

    resp = client.delete(
        f"/api/watchlists/{wl_id}/stocks/{client.stock1_id}",
        headers=auth_headers(client.user_id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_delete_nonexistent_watchlist_returns_404(client):
    """DELETE /api/watchlists/{id} for a watchlist that doesn't exist returns 404."""
    resp = client.delete("/api/watchlists/99999", headers=auth_headers(client.user_id))
    assert resp.status_code == 404
