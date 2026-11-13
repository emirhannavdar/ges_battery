from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.api import app
from auth.auth_request import get_db

client = TestClient(app)


def test_auth_token_without_token():
    response = client.post("/auth/token")
    assert response.status_code == 422          #çünkü body gönderilmedi

def test_auth_sign_without_token():
    response = client.post("/auth/sign")
    assert response.status_code == 401

def test_auth_users_me_without_token():
    response = client.get("/auth/users/me")
    assert response.status_code == 401

def test_auth_sign_missing_parameter(authenticated_client):
    response = client.post(
        "/auth/sign"
    )
    assert response.status_code == 422

def test_auth_users_me_missing_parameter(authenticated_client):
    response = authenticated_client.get(
        "/auth/users/me"
    )
    assert response.status_code == 200


def test_auth_token():
    fake = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake

    # patch istenilen kısmı geçici olarak devre dışı bırakır
    with patch("auth.auth_request.get_user_db") as mock_get_user, \
         patch("auth.auth_request.controle_hash_password", return_value=True):

        mock_get_user.return_value = {
            "username": "test",
            "hashed_password": "fake-hashed-password",
            "token_type": "Bearer",
            "access_token": "fake-access-token"
        }
        try:
            response = client.post(
                "/auth/token",
                data = {
                    "username": "test",
                    "password": "123456789"
                }
            )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_db, None)

def test_auth_sign(authenticated_client):
    fake = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake

    with patch("auth.auth_request.get_user_db", return_value=None), \
         patch("auth.auth_request.get_user_by_email", return_value=None):
        try:
            response = authenticated_client.post(
                "/auth/sign",
                json = {
                    "username": "test-user",
                    "full_name": "test user",
                    "email": "test_user@emirhannavdar.com",
                    "password": "123456"
                }
            )
            assert response.status_code == 201
        finally:
            app.dependency_overrides.pop(get_db, None)

def test_auth_token_if_not_user():
    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch("auth.auth_request.get_user_db", return_value=None):
        try:
            response = client.post(
                "/auth/token",
                data = {
                    "username": "test-user",
                    "password": "132456"
                }
            )

            assert response.status_code == 401
            assert response.json() == {"error_description": "Kullanıcı bulunamadı"}
        finally:
            app.dependency_overrides.pop(get_db, None)

def test_auth_token_disabled_user(authenticated_client):
    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch("auth.auth_request.get_user_db") as mogic_db:
        mogic_db.return_value = {
            "username": "test-user",
            "full_name": "test user",
            "email": "test@test.com",
            "hashed_password": "123456",
            "disabled": True
        }
        try:
            response = authenticated_client.post(
                "/auth/token",
                data = {
                    "username": "test-user",
                    "password": "1234465897"
                }
            )

            assert response.status_code == 401
            assert response.json() == {"error_description": "Kullanıcı aktif değil."}

        finally:
            app.dependency_overrides.pop(get_db, None)

def test_auth_token_not_true_password(authenticated_client):
    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch("auth.auth_request.get_user_db") as mogic_db, \
            patch("auth.auth_request.controle_hash_password", return_value=False):
        mogic_db.return_value = {
            "username": "test-user",
            "full_name": "test user",
            "email": "test@test.com",
            "hashed_password": "1234567",
            "disabled": False
        }
        try:
            response = authenticated_client.post(
                "/auth/token",
                data = {
                    "username": "test-user",
                    "password": "12345678"
                }
            )
            assert response.status_code == 401
            assert response.json() == {"error_description": "Şifre yanlış"}
        finally:
            app.dependency_overrides.pop(get_db, None)

