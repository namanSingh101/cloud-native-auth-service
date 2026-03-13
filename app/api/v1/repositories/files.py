from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import select,or_

from app.models.file import File,FileStatus


async def create_pending_file(
        db:AsyncSession,
        *,
        user_id:uuid.UUID,
        file_id:uuid.UUID,
        original_filename:str,
        content_type:str,
        size_bytes:int,
        s3_key:str,
        s3_bucket_name:str,
        presigned_expires_at:datetime
        )->File:
     
    file = File(
        id=file_id,
        user_id=user_id,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        s3_bucket_name=s3_bucket_name,
        s3_key=s3_key,
        status=FileStatus.pending,
        presigned_expires_at=presigned_expires_at
    ) 
    

    db.add(file)
    await db.flush()
    await db.commit()
    await db.refresh(file)
    
    return file