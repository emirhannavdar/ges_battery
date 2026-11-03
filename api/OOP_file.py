import requests

from typing import TypeVar, Generic, Optional
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from api.config import EPIAS_BASE_URI, VISUAL_CROSSING_BASE_URI, VISUAL_CROSSING_API_KEY

from error import DomainError, ExternalServiceError, AuthenticationError

T = TypeVar("T")

class RestApi(BaseModel, Generic[T]):
    success : bool
    data: Optional[T] = None
    timestamp: datetime = datetime.now(timezone(timedelta(hours=3)))
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


class OOP_Epias():
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()

    def post_TGT_token(self, username: str, password: str):
        try:
            url = "https://giris.epias.com.tr/cas/v1/tickets"

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"
            }

            payload = {
                "username": username,
                "password": password
            }

            response = self.session.post(
                url,
                headers=headers,
                data=payload,
                timeout=30
            )

            response.raise_for_status()

            token = response.text.strip()

            if not token.startswith("TGT-"):
                raise ExternalServiceError("EPİAŞ geçerli bir TGT döndürmedi.")

            self.token = token
            return self.token

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            raise ExternalServiceError(message=f"Epiaş servis hatası: {str(e)}",error_code=status_code)

    def post_PTF(self, startDate: str, endDate: str):
        try:
            if not self.token:
                raise AuthenticationError("İşlem yapabilmek için önce TGT token alınız")

            if startDate > endDate:
                raise DomainError("Başlangıç değeri bitiş değerinden büyük olamaz.")

            url = (self.base_url[:-1] + "/v1/markets/dam/data/mcp")

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "TGT": self.token
            }

            body = {
                "startDate": startDate,
                "endDate": endDate
            }

            response = self.session.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )

            response_data = response.json()
            items_list = response_data.get("items", [])

            if not items_list:
                raise DomainError("Başlangıç günü olarak bugün'ü girmelisiniz. Eğer saat 14:00'ı geçmişse bitiş olarak bir sonraki günü girebilirsiniz.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            raise ExternalServiceError(message=f"Epiaş servis hatası: {str(e)}",error_code=status_code)

    def post_KPTF(self, startDate: str):
        try:
            if not self.token:
                raise AuthenticationError("İşlem yapabilmek için önce TGT token alınız")

            url = (
                self.base_url[:-1] + "/v1/markets/dam/data/interim-mcp"
            )

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "TGT": self.token
            }

            body = {
                "startDate": startDate
            }

            response = self.session.post(
                url,
                headers=headers,
                json=body,
                timeout=30
            )

            response_data = response.json()
            items = response_data.get("items", [])

            if not items:
                raise DomainError("Eğer saat 14:00'ı geçmediyse başlangıç olarak bugün'ü girmelisiniz.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            raise ExternalServiceError(message=f"Epiaş servis hatası: {str(e)}", error_code=status_code)


epias_client = OOP_Epias(EPIAS_BASE_URI)
def get_epias_client():
    return epias_client


T = TypeVar("T")


class OOP_VisualCrossing():
    def __init__(self):
        self.token = None
        self.session = requests.Session()

    def token_varmi(self):
        if VISUAL_CROSSING_API_KEY:
            self.token = VISUAL_CROSSING_API_KEY
        else:
            raise HTTPException(
                status_code=401,
                detail="Önce VISUAL CROSSING token alınmalı"
            )
        return self.token

    def get_havadurumu(self, enlem: float, boylam: float):
        try:
            url = (
                f"{VISUAL_CROSSING_BASE_URI} + {enlem}, {boylam}"
            )
            print(url)

            data = {
                "key": self.token,
                "contentType": "json",
                "unitGroup": "metric",
                "include": "hours",
                "elements": "datetime,solarradiation,solarenergy,temp,cloudcover",
                "lang": "tr"
            }

            response = self.session.get(
                url,
                params=data
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            error_res = RestApi.error(message=str(e), code=status_code)
            raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))

    def get_havadurumu_full(
            self,
            enlem: float | None = None,
            boylam: float | None = None
    ):
        try:
            url = (
                f"{VISUAL_CROSSING_BASE_URI} + {enlem}, {boylam}"
            )

            data = {
                "key": self.token,
                "unitGroup": "metric",
                "include": "hours",
                "elements": "datetime,tempmax,tempmin,temp,cloudcover,solarradiation,solarenergy,sunrise,sunset,description,icon,feelslike,humidity,windspeed",
                "lang": "tr",
                "contentType": "json"
            }

            response = self.session.get(
                url,
                params=data
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            error_res = RestApi.error(message=str(e), code=status_code)
            raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))


weather_client = OOP_VisualCrossing()

def get_weather_client():
    return weather_client