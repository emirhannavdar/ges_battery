import hmac
import logging
import pathlib
import jwt

from api.config.config import _ACTIVE_KEY_ID, _XSECRET_KEYS
from uuid import uuid4, UUID
from datetime import timedelta, datetime, timezone
from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.database import get_db
from api.errors.exceptions import AuthenticationError, DomainError
from fastapi.security import APIKeyHeader

refresh_token_scheme = APIKeyHeader(
    name="X-Refresh-Token",
    scheme_name="RefreshToken",
    description="Refresh JWT Token",
    auto_error=False
)

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

logger = logging.getLogger(__name__)


class User(BaseModel):
    id: int
    role: str
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str | None = None
    current_access_jti: UUID | None = None
    current_refresh_jti: UUID | None = None


class UserAuth:
    def __init__(self):
        self._secret_key = _XSECRET_KEYS[_ACTIVE_KEY_ID]
        self._algorithm = "HS512"

    def _jwt_token(
            self,
            user_id: int,
            role: str,
            token_type: str = "access"
    ):
        now = datetime.now(timezone.utc)

        if token_type not in ("access", "refresh"):
            raise ValueError("Geçersiz token türü.")

        expires = (
            timedelta(minutes=15)
            if token_type == "access"
            else timedelta(days=7)
        )

        payload = {
            "sub": str(user_id),
            "role": role,
            "iat": now,     # alış tarihi
            "nbf": now,     # token başlangıç arih
            "exp": now + expires, # ne kadar zaman geçerli
            "jti": str(uuid4()),    # token'ın kimliği
            "iss": "bayraktarsolar",   # token'ı oluşturan sevişs
            "aud": "ges-api",   #tokenın kullanılacağı servis
            "type": token_type
        }

        token = jwt.encode(
            payload,
            self._secret_key,
            algorithm=self._algorithm,
            headers={"kid": _ACTIVE_KEY_ID}
        )

        return {"token": token, "payload": payload}

    def _decode_refresh_token(self, token: str) -> dict:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid or kid not in _XSECRET_KEYS:
                raise AuthenticationError("Geçersiz anahtar kimliği.")

            payload = jwt.decode(
                token,
                _XSECRET_KEYS[kid],
                algorithms=[self._algorithm],
                audience="ges-api",
                issuer="bayraktarsolar",
                options={
                    "require": [
                        "sub", "exp", "iat", "nbf",
                        "jti", "iss", "aud", "type"
                    ]
                }
            )

            if payload.get("type") != "refresh":
                raise AuthenticationError(
                    "Bu token refresh token değil."
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationError(
                "Refresh token süresi doldu. Tekrar giriş yapın."
            )

        except jwt.InvalidTokenError:
            raise AuthenticationError(
                "Geçersiz refresh token."
            )

    def __get_user(self, db: Session, user_id: int):
        try:
            result = db.execute(
                text("""
                    SELECT id, username, full_name, email, role, disabled, current_access_jti, current_refresh_jti
                    FROM users
                    WHERE id = :id
                """),
                {"id": user_id}
            )

            user_dict = result.mappings().first()

            if user_dict is None:
                return None

            return UserInDB(**dict(user_dict))

        except SQLAlchemyError:
            logger.exception("Kullanıcı sorgusu başarısız")
            raise

    def __decode_token(self,token: str) -> str | None:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid or kid not in _XSECRET_KEYS:
                raise ValueError("Geçersiz veya bilinmeyen bir anahtar kimliği.")

            secret_key = _XSECRET_KEYS[kid]

            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[self._algorithm],
                audience="ges-api",
                issuer="bayraktarsolar",
                options={
                    "require": [
                        "sub", "exp", "iat", "nbf",
                        "jti", "iss", "aud", "type"
                    ]
                }
            )

            if payload.get("type") != "access":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT süresi dolmuş.")
            return None
        except (jwt.InvalidTokenError, ValueError) as exc:
            logger.warning(
                "JWT doğrulama hatası: %s",
                type(exc).__name__
            )
            return None


    async def authenticate_user(self, token: str, db: Session):
        payload = self.__decode_token(token)

        if payload is None:
            raise AuthenticationError("geçersiz veya süresi dolmuş token.")

        user_id = payload.get("sub")

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise AuthenticationError(
                "Geçersiz token kimliği."
            )

        user = self.__get_user(db, user_id)

        if user is None:
            raise DomainError("Kullanıcı bulunamadı.")

        if user.disabled:
            raise AuthenticationError("Kullancı aktif değil")

        return User(
            **user.model_dump(
                exclude={"hashed_password"}
            )
        )


auth_client = UserAuth()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    return await auth_client.authenticate_user(token, db)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:

    if current_user.disabled:
        raise AuthenticationError("Inactive user")

    return current_user