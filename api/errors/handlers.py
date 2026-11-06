from fastapi import Request
from fastapi.responses import JSONResponse

from api.errors.exceptions import AppError

async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error_code": exc.error_code,
            "message": exc.message
        }
    )