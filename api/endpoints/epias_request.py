import requests
import logging

from fastapi import APIRouter, Query, Depends

from api.services.epias import OOP_Epias, get_epias_client
from api.services.epias_params import EpiasTGTToken

from api.errors.exceptions import AuthenticationError
from api.errors.request_errors import handle_request_error

from api.response.response import _RestApi
from api.response.epias_response_model import PTFData, KPTFData
from auth.auth import User, get_current_user
from auth.auth import get_current_active_user


logger = logging.getLogger(__name__)

epias = APIRouter()


@epias.post('/token')
async def tgt_token(
        raw: EpiasTGTToken,
        client: OOP_Epias = Depends(get_epias_client),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user)
):
    if raw.username == "" or raw.password == "":
        logger.info("Kullanıcı adı veya şifre boş bırakılamaz.")
        raise AuthenticationError("Kullanıcı adı veya şifre boş bırakılamaz.")
    try:
        token = client.post_TGT_token(raw.username, raw.password)
        logger.info("TGT Token alındı.")
        return _RestApi.ok(data=token,message="basarılı")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="EPİAŞ TGT Token")

@epias.post(
    '/PTF',
    response_model=_RestApi[PTFData]
)
def ptf(
        startDate: str = Query(..., examples="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarihi"),
        endDate: str = Query(..., examples="yyyy-aa-ggT00:00:00+03:00", description="Bitiş tarihi"),
        client: OOP_Epias = Depends(get_epias_client),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user)
):
    try:
        data = client.post_PTF(startDate, endDate)
        logger.info("PTF verileri çekildi.")
        return _RestApi.ok(data=data,message="PTF verileri çekildi")


    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="EPİAŞ PTF Data")

@epias.post(
    '/KPTF',
    response_model=_RestApi[KPTFData]
)
def kptf(
        startDate: str = Query(..., examples="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarihi"),
        client: OOP_Epias = Depends(get_epias_client),
        current_user: User = Depends(get_current_user),
        active_user: User = Depends(get_current_active_user)
):
    try:
        data = client.post_KPTF(startDate)
        logger.info("KPTF verileri çekildi.")
        return _RestApi.ok(data=data,message="Basarili")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="EPİAŞ KPTF Data")


