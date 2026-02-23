from fastapi import HTTPException,Request,status,Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas import ErrorResponse
from app.core import AppException

async def app_exception_handler(request:Request,exc:AppException)->JSONResponse:
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid request payload",
            details={"errors": exc.errors()}
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