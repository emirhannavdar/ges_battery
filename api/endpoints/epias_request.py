import requests

from fastapi import APIRouter, Query, Depends
from api.services.epias import OOP_Epias, get_epias_client
from api.services.epias_params import RestApi, EpiasTGTToken
from api.errors.exceptions import ExternalServiceError, AuthenticationError

epias = APIRouter()

@epias.post('/token')
async def tgt_token(raw: EpiasTGTToken, client: OOP_Epias = Depends(get_epias_client)):
    if raw.username == "" or raw.password == "":
        raise AuthenticationError("Kullanıcı adı ve şifre boş bırakılamaz.")
    try:
        print(raw.username)
        token = client.post_TGT_token(raw.username, raw.password)
        return RestApi.ok(data=token,message="basarılı")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message=f"Epiaş servis hatası: {str(e)}", error_code=status_code)

@epias.post('/PTF')
async def ptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarihi"),
        endDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Bitiş tarihi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_PTF(startDate, endDate)
        return RestApi.ok(data=data,message=f"PTF: {startDate}")


    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message={str(e)}, error_code=status_code)

#Burası kesinleşmemiş piyasa takas fiyaının alındığı yer /kpt
@epias.post('/KPTF')
async def kptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarhi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_KPTF(startDate)
        return RestApi.ok(data=data,message="Basarili")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        raise ExternalServiceError(message={str(e)}, error_code=status_code)


