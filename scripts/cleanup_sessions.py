import asyncio
from datetime import datetime, UTC, timedelta
from sqlalchemy import delete

from app.core.config import get_settings
from app.db.engine import AsyncSessionLocal
from app.models import RefreshSession

settings = get_settings()
RETENTION_DAYS = settings.EXPIRED_SESSION_RETENTION_DAYS


async def cleanup_expired_sessions() -> int:
    """
    Hard-deletes refresh sessions that have been expired past the retention window.
    Returns number of rows deleted.
    """

    cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
    async with AsyncSessionLocal() as session:
        try:
            stmt = (
                delete(RefreshSession)
                .where(RefreshSession.absolute_expires_at < cutoff)
                # Returns the IDs of deleted rows
                .returning(RefreshSession.id)
            )
            result = await session.execute(stmt)
            deleted_rows = result.all()
            row_count = len(deleted_rows)
            await session.commit()

            with open("/tmp/scheduler_heartbeat","w") as f:
                f.write(str(datetime.now(UTC).isoformat())) #for health check

            return row_count

        except Exception as e:
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(cleanup_expired_sessions())
