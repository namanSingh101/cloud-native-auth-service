from fastapi import APIRouter, Request, Response, status, Depends, File, UploadFile, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limiter import limiter
from app.core.dependencies import get_current_user
from app.db import get_db
from app.models import User, File
from app.schemas import FileUploadRequest, ApiResponse, UploadFileResponse

from ..services import request_upload

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


@router.post("/request-upload", response_model=ApiResponse[UploadFileResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def upload_file(request: Request, response: Response, file: FileUploadRequest, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UploadFileResponse]:
    uploaded_data = await request_upload(db=db, user=current_user, filename=file.filename, content_type=file.content_type, size_bytes=file.size_bytes)
    # file_id = uploaded_data.get("file_id")
    # expires_at = uploaded_data.get("expires_in")
    # upload_url = uploaded_data.get("presigned_url")
    # max_size_bytes=uploaded_data.max_size_bytes

    # if not file_id or not upload_url or not expires_at:
    #      raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    #         detail="File upload failed.Try again after some time",
    #     )
    return ApiResponse(
        success=True, 
        message="Upload request validated successfully", 
        data=UploadFileResponse(
            file_id=uploaded_data.file_id, 
            upload_url=uploaded_data.presigned_url, 
            expires_at=uploaded_data.expires_in, 
            max_size_bytes=uploaded_data.max_size_bytes)
            )


@router.post("/{file_id}/confirm", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def confirm_file_upload(file_id: str, request: Request, response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    pass
