from http.client import HTTPException
from fastapi.params import Depends
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth.auth import get_current_user
from database.database import get_user_role, get_db
from auth.auth import User, get_current_active_user
from api.response.response import _RestApi
from api.errors.exceptions import ForbiddenError

def admin_require_roles():
    def role_chek(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db),
            user: User = Depends(get_current_active_user)
    ):
        user_role = get_user_role(db, user.username, user.email)

        if user_role.get("role") != "admin":
            raise ForbiddenError("Bu işlem için ADMİN yetkisine ihtiyaç vardır.")
        return current_user
    return role_chek

def operator_require_roles():
    def role_chek(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db),
            user: User = Depends(get_current_active_user)
    ):
        user_role = get_user_role(db, user.username, user.email)

        if user_role.get("role") != "operator" and user_role.get("role") != "admin":
            raise ForbiddenError("Bu işlem için OPERATOR veya ADMİN yetkisine ihtiyaç vardır.")
        return current_user
    return role_chek
