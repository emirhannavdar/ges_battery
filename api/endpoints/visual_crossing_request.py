import requests

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.config.config import settings
from api.services.visual_crossing import (
    OOP_VisualCrossing,
    get_weather_client
)
from api.response.response import _RestApi
from api.errors.request_errors import handle_request_error
from api.response.weather_response_model import WeatherData
from database.weather_db import save_weather_data
from database.database import get_db
from auth.auth import get_current_user, User, get_current_active_user


visual_crossing = APIRouter()

@visual_crossing.get(
    '',
    response_model= _RestApi[WeatherData]
)
def weather(
    enlem: float= settings._ENLEM,
    boylam: float= settings._BOYLAM,
    client: OOP_VisualCrossing = Depends(get_weather_client),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_user: User = Depends(get_current_active_user)
):

    try:
        data = client.get_havadurumu(enlem, boylam)

        save_weather_data(
            db=db,
            location_id=1,
            weather_data=data
        )

        return _RestApi.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="visual_crossing")

@visual_crossing.get(
    '/weather/full',
    response_model= _RestApi[WeatherData]
)
def weather_full(
        enlem: float = settings._ENLEM,
        boylam: float = settings._BOYLAM,
        client: OOP_VisualCrossing = Depends(get_weather_client),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user)
):
    try:
        data = client.get_havadurumu_full(enlem, boylam)
        return _RestApi.ok(data=data, message="Basarili")


    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="visual_crossing")