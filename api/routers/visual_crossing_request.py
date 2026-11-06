import requests

from fastapi import APIRouter, Depends

from api.config.config import _ENLEM, _BOYLAM
from api.services.visual_crossing import (
    OOP_VisualCrossing,
    get_weather_client
)
from api.response.response import _RestApi
from api.errors.request_errors import handle_request_error
from api.response.weather_response_model import WeatherData


visual_crossing = APIRouter()

@visual_crossing.get(
    '',
    response_model= _RestApi[WeatherData]
)
def weather(
    enlem: float= _ENLEM,
    boylam: float= _BOYLAM,
    client: OOP_VisualCrossing = Depends(get_weather_client),
):
    try:
        data = client.get_havadurumu(enlem, boylam)
        return _RestApi.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="visual_crossing")

@visual_crossing.get(
    '/weather/full',
    response_model= _RestApi[WeatherData]
)
def weather_full(
        enlem: float = _ENLEM,
        boylam: float = _BOYLAM,
        client: OOP_VisualCrossing = Depends(get_weather_client)
):
    try:
        data = client.get_havadurumu_full(enlem, boylam)
        return _RestApi.ok(data=data, message="Basarili")


    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="visual_crossing")