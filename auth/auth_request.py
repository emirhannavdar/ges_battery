import logging
import pathlib
import string

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from api.errors.exceptions import AuthenticationError
from auth.auth import UserInDB, User, get_current_user, auth_client, get_current_active_user, refresh_token_scheme
from database.database import get_db, get_user_db, get_user_by_email, get_user_db_full
from hash.hash_pass import get_hashed_password, controle_hash_password
from database.database import create_user_db
from auth.roles import admin_require_roles, viewer_require_roles
from sqlalchemy import text

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
    role: str

@auth.post("/token")
async def login(
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)],

):
    user_dict = get_user_db(db, form_data.username)
    global sayac

    if not user_dict:
        sayac += 1
        if sayac > 5:
            logger.info(f"{sayac} kere hatalı giriş yapıldı.")
        return JSONResponse(
            status_code=401,
            content={
                "error_description": "Kullanıcı bulunamadı",
            }
        )

    user = UserInDB(**user_dict)

    if user.disabled:
        return JSONResponse(
            status_code=401,
            content={
                "error_description": "Kullanıcı aktif değil.",
            },
        )

    if controle_hash_password(db, password=form_data.password, username=form_data.username) != True:
        sayac += 1
        if sayac > 5:
            logger.info(f"{sayac} kere hatalı giriş yapıldı.")

        return JSONResponse(
            status_code=401,
            content={
                "error_description": "Şifre yanlış"
            }
        )

    sayac = 0

    access_token = auth_client._jwt_token(
        user_id=user_dict["id"],
        role=user_dict["role"],
        token_type="access"
    )
    try:
        db.execute(
            text("""
                    UPDATE users
                    SET current_access_jti = :current_access_jti
                    WHERE id = :id
                """
            ), {
                "current_access_jti": UUID(access_token["payload"]["jti"]),
                "id": user_dict["id"],
            }
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Access token JTI kaydedilemedi.")
        raise

    refresh_token = auth_client._jwt_token(
        user_id=user_dict["id"],
        role=user_dict["role"],
        token_type="refresh"
    )

    return {
        "access_token": access_token["token"],
        "token_type": "bearer",
        "refresh_token": refresh_token["token"]
    }

@auth.post('/refresh-access-token')
async def refresh_access_token(
    refresh_token: Annotated[
        str | None,
        Depends(refresh_token_scheme)
    ],
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise AuthenticationError("Refresh token bulunamadı")

    payload = auth_client._decode_refresh_token(refresh_token)

    if not refresh_token:
        raise AuthenticationError("Refresh token bulunamadı")

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise AuthenticationError("Geçersiz kullanıcı.")

    user = get_user_db_full(db, user_id)

    access_token = auth_client._jwt_token(
        user_id=user["id"],
        role=user["role"],
        token_type="access"
    )

    try:
        db.execute(
            text("""
                    UPDATE users
                    SET current_access_jti = :current_access_jti
                    WHERE id = :id
                """
            ), {
                "current_access_jti": UUID(access_token["payload"]["jti"]),
                "id": user["id"],
            }
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Access token JTI kaydedilemedi.")
        raise

    return {
        "username": user["username"],
        "access_token": access_token["token"],
        "token_type": "bearer",
        "jti-access_token": access_token["payload"]["jti"]
    }


@auth.post('/sign', status_code=201)
def sign_up(
        raw: SignUpForm,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user),
        user: dict = Depends(admin_require_roles()),
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

    if len(raw.password) <= 15 :
        raise HTTPException(
            status_code=400,
            detail="En az 15 karakterlik bir şifre giriniz."
        )
    if not any(char in string.punctuation for char in raw.password):
        raise HTTPException(
            status_code=400,
            detail="Şifre en az bir özel karakter içermelidir."
        )

    hashed_pass = get_hashed_password(raw.password)
    try:
        create_user_db(
            db=db,
            username=raw.username,
            full_name=raw.full_name,
            email=raw.email,
            hashed_password=hashed_pass,
            role=raw.role
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
        active_user: User = Depends(get_current_active_user),
        user: dict = Depends(viewer_require_roles())
):
    return current_user

