import hashlib
import base64
import pathlib

from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, requests
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from api.errors.exceptions import ExternalServiceError
from api.errors.request_errors import handle_request_error

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str


def hash_password(password: str, username: str):
    try:
        salt = username.encode('utf-8')
        t_sha = hashlib.sha512()
        t_sha.update(password.encode('utf-8') + salt)
        hashed_password = base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')
        return hashed_password

    except requests.exceptions.RequestException as e:
        handle_request_error(
            e,
            service_name="hash-password"
        )


def __get_user(db, hashed_password: str):
    try:
        clean_password = hashed_password.removeprefix("Token: ")

        for user_dict in db.values():
            if user_dict.get("hashed_password") == clean_password:
                return UserInDB(**user_dict)

        return None

    except requests.exceptions.RequestException as e:
        handle_request_error(
            e,
            service_name="get-user"
        )

def __decode_token(token):
    try:
        from auth.auth_request import users_db
        user = __get_user(users_db, token)

        return user

    except requests.exceptions.RequestException as e:
        handle_request_error(
            e,
            service_name="decode-token"
        )


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        user = __decode_token(token)

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

async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise ExternalServiceError("Kullanıcı aktif değil")
    return current_user

