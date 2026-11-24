from fastapi.params import Depends
from fastapi import Depends
from sqlalchemy.orm import Session
from database.database import get_user_role, get_db
from auth.auth import User, get_current_active_user
from api.errors.exceptions import ForbiddenError

def require_roles(*allowed_roles: str):

    def role_check(
        user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        if not user.role:
            raise ForbiddenError(
                "Kullanıcıya ait rol bilgisi bulunamadı."
            )

        if user.role not in allowed_roles:
            raise ForbiddenError(
                "Bu işlem için yeterli yetkiniz bulunmuyor."
            )

        return user

    return role_check


def admin_require_roles():
    return require_roles("admin")


def operator_require_roles():
    return require_roles("admin", "operator")

def viewer_require_roles():
    return require_roles("viewer", "operator", "admin")