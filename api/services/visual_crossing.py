import requests
import logging

from api.config.config import _VISUAL_CROSSING_BASE_URI, _VISUAL_CROSSING_API_KEY

from api.services.weather_params import (
    get_weather_params,
    BASIC_ELEMENTS,
    FULL_ELEMENTS
)

from api.errors.exceptions import ExternalServiceError, AuthenticationError, WeatherDataError
from api.errors.request_errors import handle_request_error


logger = logging.getLogger(__name__)


class OOP_VisualCrossing():

    def __init__(self):
        self.session = requests.Session()
        self.token = _VISUAL_CROSSING_API_KEY
        self.base_url = _VISUAL_CROSSING_BASE_URI

    def __setattr__(self, name, value):
        if name == "token" and hasattr(self, "token"):
            logger.info("Weather API token değiştirilmeye çalışıldı.")
            raise ExternalServiceError("DIKKAT: token değeri kod içinde değiştirilemez!")

        if name == "base_url" and hasattr(self, "base_url"):
            logger.info("Weather API base url değiştirilmeye çalışıldı")
            raise ExternalServiceError("DIKKAT: base url kod içinde değiştirilemez!")
        
        super().__setattr__(name, value)

    def __token_varmi(self):
        if not self.token:
            logger.info("VISUAL CROSING token yok.")
            raise AuthenticationError("Önce VISUAL CROSSING token alınmalı")

        return self.token

    def __request_weather(
        self,
        enlem: float,
        boylam: float,
        elements: str
    ):
        try:
            url = f"{self.base_url.rstrip('/')}/{enlem},{boylam}"

            data = get_weather_params(
                token=self.token,
                elements=elements
            )

            response = self.session.get(
                url,
                params=data,
                timeout=30
            )

            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            raise handle_request_error(e, service_name="visual_crossing")

        try:
            result = response.json()
        except ValueError as e:
            logger.exception("Visual Crossing geçersiz json döndürdü.")

            raise WeatherDataError("Visual crossing beklenmeyen veri frmatı döndürdü.") from e
        logger.info("Weather API verileri çekildi")

        return result


    def get_havadurumu(self, enlem: float, boylam: float):

        self.__token_varmi()

        return self.__request_weather(
            enlem=enlem,
            boylam=boylam,
            elements=BASIC_ELEMENTS
        )

    def get_havadurumu_full(self, enlem: float, boylam: float):

        self.__token_varmi()

        return self.__request_weather(
            enlem=enlem,
            boylam=boylam,
            elements=FULL_ELEMENTS
        )


__weather_client = OOP_VisualCrossing()

def get_weather_client():
    return __weather_client
