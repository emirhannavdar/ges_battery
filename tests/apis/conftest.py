import pytest
from fastapi.testclient import TestClient
from api.api import app
from auth.auth import get_current_user, get_current_active_user

@pytest.fixture
def authenticated_client():
    def fake_current_user():
        return {
            "username": "testuser",
            "is_active": True
        }

    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_current_active_user] = fake_current_user

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
