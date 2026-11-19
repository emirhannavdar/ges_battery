import os
from http.client import HTTPException

from dotenv import load_dotenv
from fastapi.params import Depends
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.auth import get_current_user
from database.database import get_user_role, get_db
from auth.auth import User, get_current_active_user


def admin_require_roles():
    def role_chek(
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db),
            user: User = Depends(get_current_active_user)
    ):
        user_role = get_user_role(db, user.username, user.email)

        if user_role.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için OPERATOR veya ADMİN yetkisine ihtiyaç vardır."
            )
        return current_user
    return role_chek







