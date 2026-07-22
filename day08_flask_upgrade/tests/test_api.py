import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.testing = True
    with flask_app.test_client() as client:
        yield client


def login(client):
    """Helper to login with demo account."""
    resp = client.post("/login", data={"username": "student", "password": "day07"}, follow_redirects=True)
    assert resp.status_code == 200
    return resp


def test_metrics_api_returns_metrics(client):
    login(client)
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert data.get("ok") is True
    metrics = data.get("metrics")
    assert isinstance(metrics, list)
    # expecting four metric cards
    assert len(metrics) == 4
    for m in metrics:
        assert "label" in m and "value" in m and "note" in m


def test_categories_api_filters(client):
    login(client)
    # use a known category from the sample CSV (e.g. "Fashion")
    resp = client.get("/api/categories?category=Fashion")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("ok") is True
    assert data.get("category") == "Fashion"
    rows = data.get("rows")
    assert isinstance(rows, list)
    # all returned rows should have 偏好品类 == "Fashion"
    for r in rows:
        # depending on localization, the key is "偏好品类"
        assert r.get("偏好品类") == "Fashion"


def test_ask_empty_question_returns_400_json_error(client):
    login(client)
    resp = client.post("/api/ask", json={"question": ""})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data is not None
    # unified error structure
    assert data.get("ok") is False
    assert "error" in data and isinstance(data.get("error"), str)