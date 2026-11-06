from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.epias_request import epias
from api.routers.visual_crossing_request import visual_crossing

from api.errors.exceptions import AppError
from api.errors.handlers import app_error_handler

from api.config.logging_config import setup_logging


setup_logging()         # logları uygulama çalışınca bir kez sertup eder. 1 kere çalıştırmam yeterli

app = FastAPI(
    title="Epias",
    description="Epias API",
    version="0.0.1"
)

app.add_exception_handler(AppError, app_error_handler)      # hataları global yakalar api de serverda kalmaz

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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


