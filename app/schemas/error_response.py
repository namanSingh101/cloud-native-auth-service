from typing import Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code:str
    message:str
    details:Optional[dict] = None


class HealthResponse(BaseModel):
    api_service:str
    redis_service:bool
    otp_service:dict
    cache_service:dict