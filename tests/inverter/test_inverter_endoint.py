from sys import path
from unittest.mock import patch, MagicMock

import pytest

from api.api import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_inverter_without_token(authenticated_client):
    response = authenticated_client.get("/inverter/data")
    assert response.status_code == 200

def test_inverter_start_without_token(authenticated_client):
    response = authenticated_client.post("/inverter/start")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "İnvertör başlatıldı."
    }

def test_inverter_not_token_start():
    response = client.post("/inverter/start")

    assert response.json() == {
        "detail": "Not authenticated"
    }
    assert response.status_code == 401

def test_inverter_reset_without_token(authenticated_client):
    response =authenticated_client.post("/inverter/reset")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Simülasyon sıfırlandı."
    }

def test_inverter_not_token_reset():
    response = client.post("/inverter/reset")

    assert response.json() == {
        "detail": "Not authenticated"
    }
    assert response.status_code == 401

def test_inverter_fault_endpoint(authenticated_client):
    with patch("simulation.simulation_manager.SimulationManager.set_inverter_fault") as mock:
        response = authenticated_client.post(
            "/inverter/fault",
            json={
                "inverter_id": "inverter_test_100123",
                "reason": "Test arızası"
            }
        )

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "message": "Inverter arıza üretti."
        }

def test_inverter_fault_value_error(authenticated_client):
    with patch("simulation.simulation_manager.SimulationManager.set_inverter_fault",
            side_effect=ValueError("Geçersiz inverter ID")) as mock_set_fault:

        response = authenticated_client.post(
            "/inverter/fault",
            json={
                "inverter_id": "inverter_test_100123",
                "reason": "Test arızası"
            }
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Geçersiz inverter ID"}

def test_inverter_fault_reset_value_error(authenticated_client):
    with patch("simulation.simulation_manager.SimulationManager.reset_inverter_fault",
               side_effect= ValueError("Inverter bulunamadı")) as mock:

        response = authenticated_client.post("/inverter/fault/reset/olmayan-inverter-test-2" )

        assert response.status_code == 400
        assert response.json() == {"detail": "Inverter bulunamadı"}

def test_inverter_reset_inverter_id(authenticated_client):
    with patch("simulation.simulation_manager.SimulationManager.reset_inverter_fault") as mock:
        response = authenticated_client.post(
            "/inverter/fault/reset/{inverter_id}",
            data={"inverter_id": "inverter_test_100123"}
        )

        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "message": "Inverter arızası sıfırlandı"
        }




