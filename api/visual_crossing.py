import requests

from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from api.config import ENLEM, BOYLAM
from api.OOP_file import OOP_VisualCrossing, get_weather_client, RestApiWeather

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
            return RestApiWeather.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        error_res = RestApiWeather.error(message=str(e), code=status_code)
        raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))


@visual_crossing.get('/weather/full')
def weather_full(enlem: float = ENLEM, boylam: float = BOYLAM, client: OOP_VisualCrossing = Depends(get_weather_client)):
    try:
        if client.token_varmi():
            data = client.get_havadurumu(enlem, boylam)
            return RestApiWeather.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        error_res = RestApiWeather.error(message=str(e), code=status_code)
        raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))