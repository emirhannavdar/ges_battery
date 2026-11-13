from fastapi.testclient import TestClient
from api.api import app
from unittest.mock import MagicMock,patch
from api.services.visual_crossing import get_weather_client


client = TestClient(app)


def test_weather_without_token():
    response = client.get("/api/v1/visual_crossing")
    assert response.status_code == 401

def test_weather_without_token_full():
    response = client.get("/api/v1/visual_crossing/weather/full")
    assert response.status_code == 401

def test_weather_missing_parameter(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/visual_crossing",
        params = {
            "enlem": "",
            "boylam": ""
        }
    )
    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        error["loc"] == ["query", "enlem"]
        for error in errors
    )

def test_weather_missing_parameter_full(authenticated_client):
    response = authenticated_client.get(
        "api/v1/visual_crossing/weather/full",
        params = {
            "enlem": "",
            "boylam": ""
        }
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["query", "enlem"]
        for error in errors
    )

def test_weather_success_full(authenticated_client):
    fake_user = MagicMock()
    fake_user.get_havadurumu_full.return_value = {
        "address": "39.97, 32.68",
        "timezone": "Europe/Istanbul",
        "days": [
            {
                "datetime": "2026-11-11",
                "temp": 7.7,
                "cloudcover": 87.0,
                "solarradiation": 7.7,
                "solarenergy": 0.0,
                "hours": [
                    {
                        "datetime": "00:00:00",
                        "temp": 7.8,
                        "cloudcover": 87.1,
                        "solarradiation": 7.8,
                        "solarenergy": 0.1,
                        "feelslike": 4,
                        "humidity": 93.19,
                        "windspeed": 1.8,
                    }
                ]
            }
        ]
    }

    app.dependency_overrides[get_weather_client] = lambda: fake_user

    try:
        response = authenticated_client.get(
            "api/v1/visual_crossing/weather/full",
            params = {
                "enlem": "39.97",
                "boylam": "32.68"
            }
        )
        assert response.status_code == 200

        body = response.json()

        assert body["success"] == True
        assert body["data"]["days"][0]["datetime"] == "2026-11-11"
        assert body["data"]["days"][0]["temp"] == 7.7
        assert body["data"]["days"][0]["cloudcover"] == 87.0
        assert body["data"]["days"][0]["solarradiation"] == 7.7
        assert body["data"]["days"][0]["solarenergy"] == 0.0
        assert body["data"]["days"][0]["hours"][0]["datetime"] == "00:00:00"
        assert body["data"]["days"][0]["hours"][0]["temp"] == 7.8
        assert body["data"]["days"][0]["hours"][0]["cloudcover"] == 87.1
        assert body["data"]["days"][0]["hours"][0]["solarradiation"] == 7.8
        assert body["data"]["days"][0]["hours"][0]["solarenergy"] == 0.1
        assert body["data"]["days"][0]["hours"][0]["feelslike"] == 4
        assert body["data"]["days"][0]["hours"][0]["humidity"] == 93.19
        assert body["data"]["days"][0]["hours"][0]["windspeed"] == 1.8

    finally:
        app.dependency_overrides.pop(get_weather_client, None)

def test_weather_success(authenticated_client):
    fake_user = MagicMock()

    fake_user.get_havadurumu.return_value = {
        "address": "39.97, 32.68",
        "timezone": "Europe/Istanbul",
        "days": [
            {
                "datetime": "2026-11-12",
                "temp": 7.7,
                "cloudcover": 87.1,
                "solarradiation": 7.7,
                "solarenergy": 0.0,
                "hours": [
                    {
                        "datetime": "00:00:00",
                        "temp": 7.8,
                        "cloudcover": 87.2,
                        "solarradiation": 7.8,
                        "solarenergy": 0.0
                    }
                ]
            }
        ]
    }

    app.dependency_overrides[get_weather_client] = lambda: fake_user

    try:
        with patch("api.endpoints.visual_crossing_request.save_weather_data") as mock_save:
            response = authenticated_client.get(
                "/api/v1/visual_crossing",
                params={
                    "enlem": "39.97",
                    "boylam": "32.68"
                }
            )

            mock_save.assert_called_once()

        assert response.status_code == 200

        body = response.json()

        assert body["success"] == True
        assert body["data"]["days"][0]["datetime"] == "2026-11-12"
        assert body["data"]["days"][0]["cloudcover"] == 87.1
        assert body["data"]["days"][0]["hours"][0]["datetime"] == "00:00:00"
        assert body["data"]["days"][0]["hours"][0]["cloudcover"] == 87.2
        assert body["data"]["days"][0]["hours"][0]["solarenergy"] == 0.0

    finally:
        app.dependency_overrides.pop(get_weather_client, None)




















