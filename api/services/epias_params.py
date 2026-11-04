from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta

T = TypeVar("T")

class RestApi(BaseModel, Generic[T]):
    success : bool
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone(timedelta(hours=3))))
    errorCode: Optional[int] = None
    message: Optional[str] = None

    @classmethod
    def ok(cls, data: T, message: Optional[str]):
        return cls(success=True, data=data, message=message)

    @classmethod
    def error(cls, message: str, code: Optional[int] = None):
        return cls(success=False, data=None, errorCode=code, message=message)

class EpiasTGTToken(BaseModel):
    username: str = ""
    password: str = ""


TGT_URL = "https://giris.epias.com.tr/cas/v1/tickets"

PTF_ENDPOINT = "/v1/markets/dam/data/mcp"
KPTF_ENDPOINT = "/v1/markets/dam/data/interim-mcp"

def get_tgt_headers():
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }

def get_tgt_body(username: str, password: str):
    return {
        "username": username,
        "password": password
    }

def get_epias_headers(token: str):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "TGT": token
    }

def get_ptf_body(startDate: str, endDate: str):
    return {
        "startDate": startDate,
        "endDate": endDate
    }

def get_kptf_body(startDate: str):
    return {
        "startDate": startDate
    }
