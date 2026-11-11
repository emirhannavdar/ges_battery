import os

from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.environ["_DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=7200, # 2 saatte bir yenilenir bağlantı
    pool_size=2,       #maks açık kalcak bağlantı
    max_overflow=20     # havuzun dışına çıkılabilir
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_db(db, username: str):
    result = db.execute(
        text("""
            SELECT username, full_name, email, hashed_password, disabled
            FROM users
            WHERE username = :username
        """),{"username": username}
    )

    return result.mappings().first()

def get_user_by_email(db: Session, email: str):
    result = db.execute(
        text("""
                SELECT id, username, email
                FROM users
                WHERE email = :email
            """),
        {"email": email}
    )

    return result.mappings().first()

def create_user_db(db, username: str, full_name: str, email: str, hashed_password: str):
    query = text(
        """
            INSERT INTO users (username, full_name, email, hashed_password, disabled)
            VALUES (:username, :full_name, :email, :hashed_password, :disabled)
        """
    )

    db.execute(
        query,
        {
            "username": username,
            "full_name": full_name,
            "email": email,
            "hashed_password": hashed_password,
            "disabled": False
        }
    )

    db.commit()

    return {"username": username, "email": email, "status": "Kullanıcı başarıyla oluşturuldu"}





