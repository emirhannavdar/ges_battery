import requests

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from api.OOP_file import RestApiEpias, OOP_Epias, EpiasTGTToken, get_epias_client

epias = APIRouter()

@epias.post('/token')
async def tgt_token(raw: EpiasTGTToken, client: OOP_Epias = Depends(get_epias_client)):
    try:
        token = client.post_TGT_token(raw.username, raw.password)
        return RestApiEpias.ok(data=token,message="basarılı")

    except Exception as e:
        error_res = RestApiEpias.error(message=str(e.detail),code=e.status_code)
        raise HTTPException(status_code=e.status_code, detail=jsonable_encoder(error_res))

@epias.post('/PTF')
async def ptf(
        startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarihi"),
        endDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Bitiş tarihi"),
        client: OOP_Epias = Depends(get_epias_client)
):
    try:
        data = client.post_PTF(startDate, endDate)
        return RestApiEpias.ok(data=data,message=f"PTF: {startDate}")

    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        error_res = RestApiEpias.error(message=str(e), code=status_code)
        raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))

#Burası kesinleşmemiş piyasa takas fiyaının alındığı yer /kpt
@epias.post('/KPTF')
async def kptf(startDate: str = Query(..., example="yyyy-aa-ggT00:00:00+03:00", description="Başlangıç tarhi"),
               client: OOP_Epias = Depends(get_epias_client)):
    try:
        data = client.post_KPTF(startDate)
        return RestApiEpias.ok(data=data,message="Basarili")


    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else None
        error_res = RestApiEpias.error(message=str(e), code=status_code)
        raise HTTPException(status_code=status_code, detail=jsonable_encoder(error_res))


