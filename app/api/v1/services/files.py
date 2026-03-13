from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, UTC, timedelta

from app.core.global_error import ResourceNotFoundError
from app.core.file_policy import get_policy_for_file
from app.core.config import get_settings
from app.models import User,File
from app.utils import generate_s3_key
from app.services import get_s3_service
from ..repositories import create_pending_file

settings = get_settings()
s3_service = get_s3_service()


async def request_upload(db: AsyncSession, user: User, filename: str, content_type: str, size_bytes: int)->dict:

    # generate file id
    file_id = uuid.uuid4()
    s3_key = generate_s3_key(
        user_id=user.id, file_id=file_id, filename=filename)

    presigned_expires_at = datetime.now(
        UTC) + timedelta(seconds=settings.PRESIGNED_URL_TTL_SECONDS)
    
     #creating db record
    file:File = await create_pending_file( 
        db=db,
        file_id=file_id,
        user_id=user.id,
        original_filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        s3_key=s3_key,
        s3_bucket_name=settings.S3_BUCKET_NAME,
        presigned_expires_at=presigned_expires_at,)

    presigned_url = await s3_service.generate_presigned_upload_url(
        s3_key=s3_key, 
        content_type=content_type, 
        size_bytes=size_bytes, 
        expires_in=settings.PRESIGNED_URL_TTL_SECONDS
        )
    
    policy = get_policy_for_file(filename=filename,content_type=content_type)
    
    return {
            "file_id": str(file.id),
            "presigned_url": presigned_url,
            "expires_in": settings.PRESIGNED_URL_TTL_SECONDS,
            "max_size_bytes":policy.max_bytes
        }
    
