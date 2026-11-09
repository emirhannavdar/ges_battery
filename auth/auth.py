import hashlib
import base64
import pathlib

from typing import Annotated
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


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
    salt = username.encode('utf-8')
    t_sha = hashlib.sha512()
    t_sha.update(password.encode('utf-8') + salt)
    hashed_password = base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')
    return hashed_password


def __get_user(db, hashed_password: str):
    clean_password = hashed_password.removeprefix("Token: ")

    for user_dict in db.values():
        if user_dict.get("hashed_password") == clean_password:
            return UserInDB(**user_dict)

    return None


def __decode_token(token):
    from auth.auth_request import users_db
    user = __get_user(users_db, token)

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = __decode_token(token)

    if not user:
        raise HTTPException(
            status_code = 401,
            detail = "Not Auth",
            headers = {"WWW-Authenticate": "Bearer"}
        )
    return user

async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(400, "Kullanıcı aktif değil")
    return current_user

