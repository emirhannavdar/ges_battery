from fastapi import FastAPI, Depends, requests
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.epias_request import epias
from api.endpoints.visual_crossing_request import visual_crossing

from auth.auth_request import auth
from auth.auth import get_current_active_user
from api.errors.exceptions import AppError
from api.errors.handlers import app_error_handler
from api.config.logging_config import setup_logging
from api.errors.request_errors import handle_request_error
from api.endpoints.simulation_request import inverter_router

setup_logging()         # logları uygulama çalışınca bir kez sertup eder. 1 kere çalıştırmam yeterli

app = FastAPI(
    title="Epias",
    description="Epias API",
    version="0.1.3",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1
    }
)

app.add_exception_handler(AppError, app_error_handler)      # hataları global yakalar api de serverda kalmaz

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
try:
    app.include_router(
        auth,
        prefix="/auth",
        tags=["auth"],
        include_in_schema=True
    )

    app.include_router(
        epias,
        prefix="/api/v1/epias",
        tags=["epias"],
        include_in_schema=True
    )

    app.include_router(
        visual_crossing,
        prefix="/api/v1/visual_crossing",
        tags=["visual_crossing"],
        include_in_schema=True
    )

    app.include_router(
        inverter_router,
        include_in_schema=True
    )


except requests.exceptions.RequestException as e:
    handle_request_error(
        e,
        service_name="visual_crossing"
    )