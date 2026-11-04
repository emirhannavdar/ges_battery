import requests
import logging

<<<<<<< HEAD:api/endpoints/epias_request.py
from fastapi import APIRouter, Query, Depends
from api.services.epias import OOP_Epias, get_epias_client
from api.services.epias_params import RestApi, EpiasTGTToken
from api.errors.exceptions import ExternalServiceError, AuthenticationError
=======
<<<<<<< Updated upstream:api/epias.py
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from api.OOP_file import RestApi, OOP_Epias, EpiasTGTToken, get_epias_client
from error import ExternalServiceError, AuthenticationError
=======
from fastapi import APIRouter, Query, Depends
from api.services.epias import OOP_Epias, get_epias_client
from api.services.epias_params import RestApi, EpiasTGTToken

from api.errors.exceptions import AuthenticationError
from api.errors.request_errors import handle_request_error


logger = logging.getLogger(__name__)
>>>>>>> Stashed changes:api/endpoints/epias_request.py
>>>>>>> fix/api:api/epias.py

epias = APIRouter()

@epias.post('/token')
async def tgt_token(raw: EpiasTGTToken, client: OOP_Epias = Depends(get_epias_client)):
    if raw.username == "" or raw.password == "":
        logger.info("Kullanıcı adı veya şifre boş bırakıldı.")
        raise AuthenticationError("Kullanıcı adı ve şifre boş bırakılamaz.")
    try:
        token = client.post_TGT_token(raw.username, raw.password)
        logger.info("TGT Token alındı.")
        return RestApi.ok(data=token,message="basarılı")

    except requests.exceptions.RequestException as e:
        handle_request_error(e, service_name="EPİAŞ TGT Token")

@epias.post('/PTF')
async def ptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarihi"),
        endDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Bitiş tarihi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_PTF(startDate, endDate)
        logger.info("PTF verileri çekildi.")
        return RestApi.ok(data=data,message=f"PTF: {startDate}")


    except requests.exceptions.RequestException as e:
        logger.error(e) # BURAYI KONTROL ET YAPIYA UYGUN DEĞİL DENEME İÇİN
        handle_request_error(e, service_name="EPİAŞ PTF Data")

#Burası kesinleşmemiş piyasa takas fiyaının alındığı yer /kpt
@epias.post('/KPTF')
async def kptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarhi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_KPTF(startDate)
        logger.info("KPTF verileri çekildi.")
        return RestApi.ok(data=data,message="Basarili")

    except requests.exceptions.RequestException as e:
        logger.info("KPTF verileri çekme sırasında hata")   # BURAYI DA KONTROL ET DENEME
        handle_request_error(e, service_name="EPİAŞ KPTF Data")


