import logging
import os
import pathlib
import jwt

from zoneinfo import ZoneInfo
from uuid import uuid4
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


BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


logger = logging.getLogger(__name__)


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    access_token: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str
    access_token: str | None = None


class UserAuth:
    def __init__(self):
        self._secret_key = os.getenv("_SECRET_KEY")
        self._algorithm = "HS512"

    def _jwt_token(self, user_id: int):
        now = datetime.now(ZoneInfo("Europe/Istanbul"))
        payload = {
            "sub": str(user_id),
            "iat": now,     # alış tarihi
            "nbf": now,     # token başlangıç arih
            "exp": now + timedelta(minutes=30), # ne kadar zaman geçerli
            "jti": str(uuid4()),    # token'ın kimliği
            "iss": "ges-battery",   # token'ı oluşturan sevişs
            "aud": "ges-battery-api",   #tokenın kullanılacağı servis
            "type": "access"
        }

        token = jwt.encode(
            payload,
            self._secret_key,
            algorithm=self._algorithm
        )

        return {"token": token, "payload": payload}


    def __get_user(self, db: Session, user_id: int):
        try:
            result = db.execute(
                text("""
                    SELECT id, username, full_name, email, access_token, hashed_password, disabled
                    FROM users
                    WHERE id = :id
                """),
                {"id": user_id}
            )

            user_dict = result.mappings().first()

            if user_dict is None:
                return None
            return User(**user_dict)

        except SQLAlchemyError:
            logger.exception("Kullanıcı sorgusu başarısız")
            raise

    def __decode_token(self,token: str) -> str | None:
        try:
            _secret_key = os.getenv("_SECRET_KEY")

            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                audience="ges-battery-api",
                issuer="ges-battery",
                options={
                    "require": [
                        "sub", "exp", "iat", "nbf",
                        "jti", "iss", "aud", "type"
                    ]
                }
            )

            if payload.get("type") != "access":
                return None

            return payload.get("sub")

        except jwt.ExpiredSignatureError:
            logger.warning("JWT süresi dolmuş.")
            return None
        except jwt.InvalidTokenError as exc:
            logger.warning(
                "JWT doğrulama hatası: %s",
                type(exc).__name__
            )
            return None


    async def authenticate_user(self, token: str, db: Session):
        user_id = self.__decode_token(token)

        if user_id is None:
            raise AuthenticationError("geçersiz veya süresi dolmuş token.")

        try:
            user_id = int(user_id)
        except ValueError:
            raise AuthenticationError(
                "Geçersiz token kimliği."
            )

        user = self.__get_user(db, user_id)

        if not user:
            raise DomainError("Kullanıcı bulunamadı.")

        return user


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
