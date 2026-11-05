import requests
import logging

from fastapi import APIRouter, Query, Depends
from api.services.epias import OOP_Epias, get_epias_client
from api.services.epias_params import RestApi, EpiasTGTToken

from api.errors.exceptions import AuthenticationError
from api.errors.request_errors import handle_request_error


logger = logging.getLogger(__name__)

epias = APIRouter()

@epias.post('/token')
async def tgt_token(raw: EpiasTGTToken, client: OOP_Epias = Depends(get_epias_client)):
    if raw.username == "" or raw.password == "":
        logger.info("Kullanıcı adı veya şifre boş bırakılamaz.")
        raise AuthenticationError("Kullanıcı adı veya şifre boş bırakılamaz.")
    try:
        token = client.post_TGT_token(raw.username, raw.password)
        logger.info("TGT Token alındı.")
        return RestApi.ok(data=token,message="basarılı")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="EP─░A┼Ş TGT Token")

@epias.post('/PTF')
async def ptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Ba┼şlang─▒├ğ tarihi"),
        endDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Biti┼ş tarihi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_PTF(startDate, endDate)
        logger.info("PTF verileri çekildi.")
        return RestApi.ok(data=data,message=f"PTF: {startDate}")


    except requests.exceptions.RequestException as e:
        logger.error(e) # BURAYI KONTROL ET YAPIYA UYGUN DE─Ş─░L DENEME ─░├ç─░N
        handle_request_error(e, service_name="EPİAŞ PTF Data")

@epias.post('/KPTF')
async def kptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Ba┼şlang─▒├ğ tarhi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_KPTF(startDate)
        logger.info("KPTF verileri çekildi.")
        return RestApi.ok(data=data,message="Basarili")

    except requests.exceptions.RequestException as e:
        logger.info("KPTF verileri çekme sırasında hata")   # BURAYI DA KONTROL ET DENEME
        handle_request_error(e, service_name="EPİAŞ KPTF Data")


