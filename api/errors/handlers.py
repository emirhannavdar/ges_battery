from fastapi import Request
from fastapi.responses import JSONResponse

from api.errors.exceptions import AppError
from api.response.response import _RestApi

async def app_error_handler(request: Request, exc: AppError):
    response = _RestApi.error(
        message=exc.message,
        code=exc.error_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json")
    )