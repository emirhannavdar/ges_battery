from urllib.request import Request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.epias_request import epias
from api.endpoints.visual_crossing_request import visual_crossing

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from error import DomainError, ExternalServiceError, AuthenticationError

# aşağıdaki kütüphaneler except için düzeltilicek buralar
from api.services.epias_params import RestApi
from api.services.weather_params import RestApi


app = FastAPI(
    title="Epias",
    description="Epias API",
    version="0.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, raw: DomainError):
    error_payload = RestApi.error(
        message=raw.message,
        code=raw.error_code
    )

    return JSONResponse(
        status_code=raw.error_code,
        content=jsonable_encoder(error_payload)
    )

@app.exception_handler(ExternalServiceError)
async def service_error_handler(request: Request, raw: ExternalServiceError):
    error_payload = RestApi.error(
        message=raw.message,
        code=raw.error_code
    )

    return JSONResponse(
        status_code=raw.error_code,
        content=jsonable_encoder(error_payload)
    )



@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, raw: AuthenticationError):
    error_payload = RestApi.error(
        message=raw.message,
        code=raw.error_code
    )

    return JSONResponse(
        status_code=raw.error_code,
        content=jsonable_encoder(error_payload)
    )



app.include_router(
    epias,
    prefix="/api/v1/epias",
    tags=["epias"]
)

app.include_router(
    visual_crossing,
    prefix="/api/v1/visual_crossing",
    tags=["visual_crossing"]
)


