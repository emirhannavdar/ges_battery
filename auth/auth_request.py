from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import os
import pathlib

from dotenv import load_dotenv

from auth.auth import (
    UserInDB,
    hash_password,
    User,
    get_current_user
)


BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

users_db = {
    "emirhannavdar": {
        "username": "emirhannavdar",
        "full_name": "Emirhan Navdar",
        "email": "emirhannavdar0@gmail.com",
        "hashed_password": os.getenv("_HASH_PASSWORD"),
        "disabled": False
    }
}

auth = APIRouter()


@auth.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(400, "yanlış username veya password")
    user = UserInDB(**user_dict)
    hashed_password = hash_password(form_data.password, form_data.username)

    if not hashed_password == user.hashed_password:
        raise HTTPException(400, "yanlış username veya password")

    return {
        "access_token": user.username,
        "token_type": "bearer"
    }


@auth.get('/users/me')
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user