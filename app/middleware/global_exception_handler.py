from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request,status
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core import AppException
from fastapi.responses import JSONResponse
from app.schemas import ErrorResponse


class UnhandledExceptionMiddleware(BaseHTTPMiddleware):
    '''
    Middle to catch any unhandled exceptions
    This runs before ServerErrorMiddlware , preventing duplicate logging
    '''
    
    async def dispatch(self,request:Request,call_next):
        try:
             
             response = await call_next(request)
             return response
        except (RateLimitExceeded,AppException,StarletteHTTPException,RequestValidationError) as e:  
            
            raise 
        except Exception as exc:
            return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                message="An Unexpected error occured",
            ).model_dump(),
    )