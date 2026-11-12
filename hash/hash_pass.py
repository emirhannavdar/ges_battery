from pwdlib import PasswordHash
from pydoc import text
from typing import Annotated
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.database import get_db

password_hash = PasswordHash.recommended()

def get_hashed_password(password: str):
    return password_hash.hash(password)

def controle_hash_password(db: Annotated[Session, Depends(get_db)], password: str, username: str):
    result = db.execute(
        text("""
            SELECT hashed_password
            FROM users
            WHERE username = :username
        """), {"username": username}
    )
    db_hashed_password = result.scalar_one_or_none()

    if not db_hashed_password:
        return False

    return password_hash.verify(password, db_hashed_password)