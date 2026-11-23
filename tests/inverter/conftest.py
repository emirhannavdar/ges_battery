import pytest
import fakeredis

from unittest.mock import patch
from fastapi.testclient import TestClient
from api.api import app
from auth.auth import get_current_user, get_current_active_user
from auth.auth import User


@pytest.fixture(autouse=True)
def mock_redis():
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    with patch("auth.auth_request.redis_client", fake_redis):
        yield fake_redis

@pytest.fixture
def authenticated_client():

    def fake_current_user():
        return User(
            id=1,
            role="admin",
            username="testuser",
            email="testuser@example.com",
            full_name="Test User",
            access_token=None,
            disabled=False
        )

    previous_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_current_active_user] = fake_current_user

    try:
        with patch(
                "auth.roles.get_user_role",
            return_value={"role": "admin"}
        ):
            with TestClient(app) as client:
                yield client

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
