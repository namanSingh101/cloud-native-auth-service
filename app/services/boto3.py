import asyncio
from functools import partial
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from datetime import timedelta

from app.core.config import get_settings

settings = get_settings()


class S3Service:
    """
    Wraps boto3 S3 client.

    All methods are async — sync boto3 calls are offloaded to a thread
    pool executor so they never block the event loop.

    boto3.Session().client() is used instead of the global boto3.client()
    because sessions isolate credentials and are safer in threaded contexts.
    """

    def __init__(self) -> None:
        self._client = boto3.Session().client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    async def _run(self, func, **kwargs):
        """Offload a sync boto3 call to the default thread pool executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, **kwargs))

    async def generate_presigned_upload_url(
        self,
        s3_key: str,
        content_type: str,
        size_bytes: int,
        expires_in: int =settings.PRESIGNED_URL_TTL_SECONDS,   # 15 min or 900 sec
    ) -> str:
        """
        Generate a presigned PUT URL for direct client → S3 upload.

        ContentType and ContentLength are locked into the signature —
        client cannot upload a different type or oversized file.
        """
        url = await self._run(
            self._client.generate_presigned_url,
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": s3_key,
                "ContentType": content_type,
                "ContentLength": size_bytes,
            },
            ExpiresIn=expires_in,
        )
        return url

    async def object_exists(self, s3_key: str) -> bool:
        """
        Check whether an object exists in S3 without downloading it.
        Uses head_object — no data transfer cost.
        """
        try:
            await self._run(
                self._client.head_object,
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise   # re-raise unexpected errors (403, 500, etc.)

    async def get_object_metadata(self, s3_key: str) -> dict:
        """
        Return S3 object metadata (ContentLength, ContentType, ETag etc.)
        Used at confirm time to overwrite client-declared size with real value.
        """
        response = await self._run(
            self._client.head_object,
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
        )
        return {
            "size_bytes": response["ContentLength"],
            "content_type": response["ContentType"],
            "etag": response.get("ETag", "").strip('"'),
        }

    async def fetch_first_bytes(self, s3_key: str, num_bytes: int = 8) -> bytes:
        """
        Fetch only the first N bytes of an object.
        Used for magic byte validation at confirm time — never downloads full file.
        """
        response = await self._run(
            self._client.get_object,
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Range=f"bytes=0-{num_bytes - 1}",
        )
        return response["Body"].read()

    async def delete_object(self, s3_key: str) -> None:
        """
        Hard-delete an object from S3.
        Called when FileRecord is marked deleted=True.
        """
        await self._run(
            self._client.delete_object,
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
        )


# single instance — import this everywhere
s3_service = S3Service()

def get_s3_service()->S3Service:
    return s3_service