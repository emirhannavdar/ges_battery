import requests
import logging

from api.config.config import VISUAL_CROSSING_BASE_URI, _VISUAL_CROSSING_API_KEY

from api.services.weather_params import (
    get_weather_params,
    BASIC_ELEMENTS,
    FULL_ELEMENTS
)

from api.errors.exceptions import ExternalServiceError, AuthenticationError, WeatherDataError


logger = logging.getLogger(__name__)


class OOP_VisualCrossing():

    def __init__(self):
        self.session = requests.Session()
        self.token = _VISUAL_CROSSING_API_KEY

    def __setattr__(self, name, value):
        if name == "token" and hasattr(self, "token"):
            logger.info("Weather API token değiştirilmeye çalışıldı.")
            raise ExternalServiceError("DİKKAT: token değeri kod içinde değiştirilemez!")

        super().__setattr__(name, value)

    def token_varmi(self):
        if not self.token:
            raise AuthenticationError("Önce VISUAL CROSSING token alınmalı")

        return self.token

    def __request_weather(
        self,
        enlem: float,
        boylam: float,
        elements: str
    ):
        try:
            url = f"{VISUAL_CROSSING_BASE_URI}{enlem},{boylam}"

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

            logger.info("Weather api verileri çekildi.")
            return response.json()

        except requests.exceptions.RequestException as e:
            raise WeatherDataError("Geçersiz istek.")

    def get_havadurumu(self, enlem: float, boylam: float):

        self.token_varmi()

        return self.__request_weather(
            enlem=enlem,
            boylam=boylam,
            elements=BASIC_ELEMENTS
        )

    def get_havadurumu_full(self, enlem: float, boylam: float):

        self.token_varmi()

        return self.__request_weather(
            enlem=enlem,
            boylam=boylam,
            elements=FULL_ELEMENTS
        )


weather_client = OOP_VisualCrossing()

def get_weather_client():
    return weather_client