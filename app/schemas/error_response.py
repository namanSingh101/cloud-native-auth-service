from typing import Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code:str
    message:str
    details:Optional[dict] = None


class HealthResponse(BaseModel):
    status:str