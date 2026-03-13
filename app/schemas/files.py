from __future__ import annotations
from pydantic import BaseModel,Field,field_validator,model_validator
from pathlib import Path
from datetime import datetime
import re
import uuid

from app.core.file_policy import get_policy_for_file


class FileUploadRequest(BaseModel):
    filename:str = Field(min_length=1, max_length=255)
    content_type:str
    size_bytes:int = Field(gt=0)

    @field_validator("filename")
    @classmethod
    def sanitize_filename(cls,value:str)->str:
        value = Path(value).name.strip()

        if not value:
            raise ValueError("Invalid filename")
        
        if not re.match(r"^[a-zA-Z0-9._-]+$",value):
            raise ValueError("Filename contains unsupported characters")
        
        return value
    
    @field_validator("content_type")
    @classmethod
    def normalize_content_type(cls, value: str) -> str:
        # strip MIME params: "image/jpeg; charset=utf-8" → "image/jpeg"
        return value.split(";")[0].strip().lower()


    @model_validator(mode="after")
    def validate_file_policy(self) -> FileUploadRequest:
        #   - extension present and supported
        #   - extension matches content_type
        #   - returns policy with per-type size limit
       
            policy = get_policy_for_file(self.filename,self.content_type)

            if self.size_bytes > policy.max_bytes:
                limit_mb = policy.max_bytes // (1024 * 1024)
                raise ValueError(f"File exceeds maximum allowed size of {limit_mb}MB")
        
            return self
        


class UploadFileResponse(BaseModel):
    file_id:uuid.UUID
    upload_url:str
    expires_at:datetime
    max_size_bytes: int 

class FileConfirmResponse(BaseModel):

    file_id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int             # real value from S3, not client-declared
    status: str
    uploaded_at: datetime