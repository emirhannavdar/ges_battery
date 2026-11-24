import logging
import pathlib
import string
import redis

from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from api.errors.exceptions import AuthenticationError
from auth.auth import UserInDB, User, get_current_user, auth_client, get_current_active_user, refresh_token_scheme
from database.database import get_db, get_user_db, get_user_by_email, get_user_db_full
from hash.hash_pass import get_hashed_password, controle_hash_password
from database.database import create_user_db
from auth.roles import admin_require_roles, viewer_require_roles
from api.config.config import Config

BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

auth = APIRouter()

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
MAX_ATTEMPTS = Config._MAX_ATTEMPTS
BLOCK_DURATION = Config._BLOCK_DURATION

logger = logging.getLogger(__name__)

class SignUpForm(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    role: str

@auth.post("/token")
async def login(
        request: Request,
        response: Response,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[Session, Depends(get_db)],

):
    client_ip = request.client.host
    redis_key = f"login_fail:{client_ip}:{form_data.username}"

    attempts = redis_client.get(redis_key)
    if attempts and int(attempts) >= MAX_ATTEMPTS:
        kalan_sure = redis_client.ttl(redis_key)
        logger.warning(f"Bloklu giriş denemesi: {form_data.username} ({client_ip}) - Kalan: {kalan_sure}sn")
        return JSONResponse(
            status_code=429,
            content={
                "error_description": f"Çok fazla hatalı giriş. {kalan_sure} saniye sonra tekrar deneyin."
            }
        )


    user_dict = get_user_db(db, form_data.username)

    if not user_dict:
        current_attemps = redis_client.incr(redis_key)
        if current_attemps == 1:
            redis_client.expire(redis_key, BLOCK_DURATION)

        return JSONResponse(
            status_code=401,
            content={"error_description": "Kullanıcı bulunamadı."}
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
        current_attempts = redis_client.incr(redis_key)
        if current_attempts == 1:
            redis_client.expire(redis_key, BLOCK_DURATION)

        if current_attempts>=MAX_ATTEMPTS:
            logger.info(f"{current_attempts} kere hatalı giriş yapıldı, Kullanıcı bloklandı.")
            return JSONResponse(
                status_code=429,
                content={
                    "error_description": f"Bloklandınız. {BLOCK_DURATION // 60} dakika sonra tekrar deneyiniz."
                }
            )
        return JSONResponse(
            status_code=401,
            content={
                "error_description": "Şifre yanlış."
            }
        )

    redis_client.delete(redis_key)

    access_token = auth_client._jwt_token(
        db,
        user_id=user_dict["id"],
        role=user_dict["role"],
        token_type="access"
    )

    refresh_token = auth_client._jwt_token(
        db,
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

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise AuthenticationError("Geçersiz kullanıcı.")

    user = get_user_db_full(db, user_id)

    if not user:
        raise AuthenticationError("Kullanıcı bulunamadı. Yönetici ile iletişime geçiniz.")

    if user["disabled"]:
        raise AuthenticationError("Kullanıcı aktif değil. Yönetici ile iletişime geçiniz.")

    db_jti = str(user["refresh_jti"]).strip() if user.get("refresh_jti") else ""
    payload_jti = str(payload.get("jti", "")).strip()

    if db_jti != payload_jti:
        raise AuthenticationError("Geçersiz veya süresi dolmuş refresh token.")

    access_token = auth_client._jwt_token(
        db,
        user_id=user["id"],
        role=user["role"],
        token_type="access"
    )

    return {
        "username": user["username"],
        "access_token": access_token["token"],
        "token_type": "bearer"
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

