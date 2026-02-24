from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.schemas import ErrorResponse
from app.utils import add_duration

async def rate_limit_exceeded_handler(request: Request,exc: RateLimitExceeded) -> JSONResponse:
    #print("Rate limit exceeded")

    #print(exc)
    
    parts = exc.detail.split(" per ")  #10 per 1 minute --> 10 , 1 minute
    retry_after = str(parts[1].strip())
    retry_limit = str(parts[0].strip())


    #calculating reset at time values
    reset_at = add_duration(retry_after)
    #print(f"{reset_at}")

    response =  JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=ErrorResponse(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            details={
                "retry_after": retry_after,
                "resets_at": reset_at
            }
        ).model_dump()

    )

    response.headers["Retry-After"] = retry_after
    response.headers["X-RateLimit-Limit"] = retry_limit
    response.headers["X-RateLimit-Remaning"] = "0"

    return response

