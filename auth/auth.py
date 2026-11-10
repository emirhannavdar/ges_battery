import logging
import hashlib
import base64
import pathlib
import requests

from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from api.errors.request_errors import handle_request_error
from database.database import get_db

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


logger = logging.getLogger(__name__)


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class UserAuth:
    def __init__(self):
        pass


    def hash_password(self, password: str, username: str):
        try:
            salt = username.encode('utf-8')     # byte çevirmek gerekiyor
            t_sha = hashlib.sha512()
            t_sha.update(password.encode('utf-8') + salt)
            hashed_password = base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')
            return hashed_password

        except requests.exceptions.RequestException as e:
            handle_request_error(
                e,
                service_name="hash-password"
            )


    def __get_user(self, db: Session, hashed_password: str):
        try:
            result = db.execute(
                text("""
                    SELECT username, full_name, email,hashed_password, disabled
                    FROM users
                    WHERE hashed_password = :hashed_password
                """),
                {"hashed_password": hashed_password}
            )

            user_dict = result.mappings().first()

            if user_dict is None:
                return None

            return UserInDB(**user_dict)


        except SQLAlchemyError:
            logger.exception("Kullanıcı sorgusu başarısız")
            raise

    def __decode_token(self,token: str,db: Session):
        return self.__get_user(db, token)



    async def authenticate_user(self, token: str, db: Session):
        try:
            user = self.__decode_token(token, db)

            if not user:
                raise HTTPException(
                    status_code = 401,
                    detail = "Not Auth",
                    headers = {"WWW-Authenticate": "Bearer"}
                )
            return user

        except requests.exceptions.RequestException as e:
            handle_request_error(
                e,
                service_name="get-current-user"
            )

auth_client = UserAuth()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    return await auth_client.authenticate_user(token, db)


async def get_current_active_user(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
) -> User:

    if current_user.disabled:
        raise HTTPException(
            status_code=403,
            detail="Inactive user"
        )

    return current_user
