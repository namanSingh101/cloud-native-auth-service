from fastapi import HTTPException,Request,status,Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import json

from app.core.global_error import AppException
from app.schemas import ErrorResponse


async def app_exception_handler(request:Request,exc:AppException)->JSONResponse:
    print("app exce")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).model_dump(exclude_none=True)
    )
async def http_exception_handler(request: Request, exc: HTTPException)->JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code="HTTP_EXCEPTION",
            message=exc.detail,
        ).model_dump(exclude_none=True),
        headers=exc.headers or None
    )

async def validation_exception_handler(request:Request,exc:RequestValidationError)->JSONResponse:
    print("app exce 1")
    errors = json.loads(json.dumps(exc.errors(), default=str))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid request payload",
            details={"errors": errors}
        ).model_dump(exclude_none=True)
    )

async def unhandled_exception_handler(request: Request, exc: Exception)->JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="Something went wrong",
        ).model_dump(exclude_none=True),
    )