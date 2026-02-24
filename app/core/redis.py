import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from pydantic import EmailStr

from app.core import get_settings, DatabaseError

settings = get_settings()


class RedisManager:

    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def init(self):
        """Call once on startup to initialize the pool."""
        self._pool = aioredis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB_OTP,
            max_connections=20,
            decode_responses=True
        )
        self._client = aioredis.Redis(connection_pool=self._pool)

        await self.ping()
        #print(type(self._client))

    async def close(self):
        """Close pool on shutdown"""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.aclose()

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def ping(self) -> bool:
        self._ensure_client()

        if not self._client:
            raise DatabaseError("Redis not initialized")
        try:
            return bool(await self._client.ping())  # type: ignore
        except Exception as e:
            raise DatabaseError(f"Redis ping failed: {e}")

    def get_client(self) -> Redis:
        """Returns a Redis client using the shared pool."""
        self._ensure_client()
        return self._client  # type: ignore

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _ensure_client(self):
        """Raise early if Redis was never initialized."""
        if self._client is None:
            raise DatabaseError(
                "Redis is not initialized. Call await redis_manager.init() on startup.")

    @staticmethod
    def _otp_key(email: EmailStr) -> str:
        return f"{settings.OTP_KEY_PREFIX}{email}"
    
    # -------------------------------------------------------------------------
    # OTP operations
    # -------------------------------------------------------------------------

    """Store otp"""

    async def set_otp(self, email: EmailStr, hashed_otp: str, ttl: int = settings.OTP_TTL_SECONDS) -> None:
        self._ensure_client()
        await self._client.set(self._otp_key(email=email), hashed_otp, ex=ttl) # type: ignore

    """Get otp"""

    async def get_otp(self, email: EmailStr) -> str | None:
        self._ensure_client()
        return await self._client.get(self._otp_key(email=email)) # type: ignore

    """Delete otp"""

    async def delete_otp(self, email: EmailStr):
        self._ensure_client()
        await self._client.delete(self._otp_key(email=email)) # type: ignore

    """Check exists"""

    async def otp_exist(self, email: EmailStr) -> bool:
        self._ensure_client()
        return await self._client.exists(self._otp_key(email)) == 1  # type: ignore
    


#Singletone instance 
redis_manager = RedisManager()

def get_redis_manager()->RedisManager:
    return redis_manager
