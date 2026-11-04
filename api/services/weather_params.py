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


BASIC_ELEMENTS = (
    "datetime,solarradiation,solarenergy,temp,cloudcover"
)

FULL_ELEMENTS = (
    "datetime,tempmax,tempmin,temp,cloudcover,"
    "solarradiation,solarenergy,sunrise,sunset,"
    "description,icon,feelslike,humidity,windspeed"
)

def get_weather_params(token: str, elements: str):

    return {
        "key": token,
        "contentType": "json",
        "unitGroup": "metric",
        "include": "hours",
        "elements": elements,
        "lang": "tr"
    }