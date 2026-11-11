import logging
import pathlib

from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from auth.auth import UserInDB, User, get_current_user, auth_client, get_current_active_user
from api.errors.exceptions import AuthenticationError
from database.database import get_db, get_user_db, get_user_by_email

from hash.hash_pass import get_hashed_password, controle_hash_password
from database.database import create_user_db


BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')


auth = APIRouter()

logger = logging.getLogger(__name__)

sayac = 0

class SignUpForm(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

@auth.post("/token")
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)]
):

    user_dict = get_user_db(db, form_data.username)
    global sayac

    if not user_dict:
        sayac += 1
        if sayac > 5:
            logger.info(f"{sayac} kere hatalı giriş yapıldı.")
        raise AuthenticationError("yanlış username")

    user = UserInDB(**user_dict)

    test = controle_hash_password(db, password=form_data.password, username=form_data.username)

    if test != True:
        sayac += 1
        if sayac > 5:
            logger.info(f"{sayac} kere hatalı giriş yapıldı.")

        raise AuthenticationError("yanlış password")

    sayac = 0

    token_data = auth_client._hash_password(form_data.username)

    logger.info(
        "PostgreSQL kullanıcı sorgusu tamamlandı. username= %s, fullname= %s email= %s",
        form_data.username, user_dict.full_name, user_dict.email
    )

    try:
        db.execute(
            text("""
                    UPDATE users 
                    SET access_token = :access_token 
                    WHERE username = :username
                """),
            {"access_token": token_data["access_token"], "username": user.username},
        )
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise

    return {
        "access_token": token_data["access_token"],
        "token_type": "bearer",
        "username": user.username
    }


@auth.post('/sign', status_code=201)
def sign_up(
        raw: SignUpForm,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user)
):
    existing_user = get_user_db(db, raw.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")

    existing_email = get_user_by_email(db, raw.email)

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Bu e-posta adresi zaten kayıtlı."
        )

    hashed_pass = get_hashed_password(raw.password)
    try:
        new_user = create_user_db(
            db=db,
            username=raw.username,
            full_name=raw.full_name,
            email=raw.email,
            hashed_password=hashed_pass,
        )

    except IntegrityError:
        db.rollback()

        logger.warning(
            "Kullanıcı oluşturulurken benzersiz alan çakışması oluştu."
        )

        raise HTTPException(
            status_code=409,
            detail="Kullanıcı adı veya e-posta adresi zaten kayıtlı."
        )

    logger.info(
        f"{raw.username} adında yeni kullanıcı oluşturuldu."
    )

    return {
        "message": "Kullanıcı başarıyla oluşturuldu.",
        "username": raw.username,
        "email": raw.email
    }


@auth.get('/users/me')
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_user)],
        active_user: User = Depends(get_current_active_user)
):
    return current_user

