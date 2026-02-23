from typing import Optional,Generic,TypeVar
from pydantic import BaseModel,ConfigDict

T = TypeVar("T")

class ApiResponse(BaseModel,Generic[T]):
    success:bool
    message:Optional[str] = None
    data:Optional[T] = None

    model_config = ConfigDict(from_attributes=True)