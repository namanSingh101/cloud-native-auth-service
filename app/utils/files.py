from fastapi import HTTPException, UploadFile, status
from uuid import UUID
import os

from app.core.config import get_settings

settings = get_settings()

def generate_s3_key(user_id: UUID, file_id: UUID, filename: str)-> str:
    #Format: uploads/{user_id}/{file_id}.{ext}

    ext = os.path.splitext(filename)[-1].lstrip(".").lower() or "bin"

    return f"uploads/{user_id}/{file_id}.{ext}"
