import requests

from fastapi import APIRouter, Depends
from api.config.config import ENLEM, BOYLAM
from api.services.visual_crossing import OOP_VisualCrossing, get_weather_client, RestApi
from error import ExternalServiceError

visual_crossing = APIRouter()

@visual_crossing.get('')
def weather(
    enlem: float= ENLEM,
    boylam: float= BOYLAM,
    client: OOP_VisualCrossing = Depends(get_weather_client),
):
    try:
        if client.token_varmi():
            data = client.get_havadurumu(enlem, boylam)
            return RestApi.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message={str(e)}, error_code=status_code)

@visual_crossing.get('/weather/full')
def weather_full(
        enlem: float = ENLEM,
        boylam: float = BOYLAM,
        client: OOP_VisualCrossing = Depends(get_weather_client)
):
    try:
        if client.token_varmi():
            data = client.get_havadurumu_full(enlem, boylam)
            return RestApi.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message={str(e)}, error_code=status_code)