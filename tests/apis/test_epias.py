from fastapi.testclient import TestClient
from api.api import app
from unittest.mock import MagicMock
from api.services.epias import get_epias_client

client = TestClient(app)


def test_epias_without_token():
    response = client.post("/api/v1/epias/token")
    assert response.status_code == 401

def test_epias_ptf_without_token():
    response = client.post("/api/v1/epias/PTF")
    assert response.status_code == 401

def test_epias_kptf_without_token():
    response = client.post("/api/v1/epias/KPTF")
    assert response.status_code == 401

def test_epias_kptf_missing_date(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/epias/KPTF"
    )
    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        error["loc"] == ["query", "startDate"]
        for error in errors
    )

def test_epias_ptf_success(authenticated_client):
    fake_epias = MagicMock()
    fake_epias.post_PTF.return_value = {
        "items": [
            {
                "date": "2026-11-11",
                "hour": "00:00",
                "price": 1500.0,
                "priceUsd": 1500.0,
                "priceEur": 1500.0,
            }
        ]
    }

    app.dependency_overrides[get_epias_client] = lambda: fake_epias

    try:
        response = authenticated_client.post(
            "api/v1/epias/PTF",
            params = {
                "startDate": "2026-11-11T00:00:00+03:00",
                "endDate": "2026-11-12T00:00:00+03:00"
            }
        )

        assert response.status_code == 200

        body = response.json()

        assert body["success"] is True
        assert body["data"]["items"][0]["price"] == 1500.0

        fake_epias.post_PTF.assert_called_once_with("2026-11-11T00:00:00+03:00", "2026-11-12T00:00:00+03:00")

    finally:
        app.dependency_overrides.pop(get_epias_client, None)

def test_epias_kptf_success(authenticated_client):
    fake_epias = MagicMock()

    fake_epias.post_KPTF.return_value = {
        "items": [
            {
                "date": "2026-11-11",
                "hour": "00:00",
                "marketTradePrice": 1500.0
            }
        ]
    }

    app.dependency_overrides[get_epias_client] = lambda: fake_epias

    try:
        response = authenticated_client.post(
            "/api/v1/epias/KPTF",
            params={
                "startDate": "2026-11-11T00:00:00+03:00"
            }
        )

        assert response.status_code == 200

        body = response.json()

        assert body["success"] is True
        assert body["data"]["items"][0]["marketTradePrice"] == 1500.0


        fake_epias.post_KPTF.assert_called_once_with("2026-11-11T00:00:00+03:00")
    finally:
        app.dependency_overrides.pop(get_epias_client, None)

def test_epias_token_success(authenticated_client):
    fake_epias = MagicMock()

    fake_epias.post_TGT_token.return_value = "123456"
    app.dependency_overrides[get_epias_client] = lambda: fake_epias

    try:
        response = authenticated_client.post(
            "/api/v1/epias/token",
            json = {
                "username": "testuser",
                "password": "123456"
            }
        )

        assert response.status_code == 200
        body = response.json()

        assert body["success"] is True
        assert body["data"] == "123456"
        assert body["message"] == "basarılı"

        fake_epias.post_TGT_token.assert_called_once_with("testuser", "123456")
    finally:
        app.dependency_overrides.pop(get_epias_client, None)







