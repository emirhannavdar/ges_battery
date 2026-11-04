import requests

from fastapi import APIRouter, Depends
<<<<<<< Updated upstream:api/visual_crossing.py
from api.config import ENLEM, BOYLAM
from api.OOP_file import OOP_VisualCrossing, get_weather_client, RestApi
from error import ExternalServiceError
=======
from api.config.config import ENLEM, BOYLAM
from api.services.visual_crossing import OOP_VisualCrossing, get_weather_client
from api.services.weather_params import RestApi
from api.errors.request_errors import handle_request_error
>>>>>>> Stashed changes:api/endpoints/visual_crossing_request.py

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
            data = client.get_havadurumu(enlem, boylam)
            return RestApi.ok(data=data, message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message={str(e)}, error_code=status_code)