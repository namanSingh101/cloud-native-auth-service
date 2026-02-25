from __future__ import annotations
import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from pydantic import EmailStr

from app.core import get_settings, DatabaseError

settings = get_settings()

#Singleton class 
class RedisManager:

    _instance: RedisManager | None = None

    #we have used "RedisManager" because there is not RedisManager instance type before the class is defined 
    # to avoid the "RedisManager" string quotation we can use from __future__ import annotations
    #This makes all annotations in the file lazy (evaluated as strings automatically), so you never need quotes for forward references again

    def __new__(cls)-> RedisManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)  #the __new__() method allocated the memory and return the object/instance of the class 
        return cls._instance

    def __init__(self):
        #if  _initialized is not used then every time we call for object it will set all variables with none 
        #to avoid this during first time when instance is created we set the _initialized = True 
        if not hasattr(self,"_initialized"):   
            self._pool: ConnectionPool | None = None
            self._client: Redis | None = None
            self._initialized = True

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

    async def set_otp(self, email: EmailStr, hashed_otp: str, ttl: int = settings.OTP_TTL_SECONDS) -> None:
        self._ensure_client()
    
        await self._client.set(self._otp_key(email=email), hashed_otp, ex=ttl) # type: ignore

    async def get_otp(self, email: EmailStr) -> str | None:
        self._ensure_client()
     
        return await self._client.get(self._otp_key(email=email)) # type: ignore

    async def delete_otp(self, email: EmailStr):
        self._ensure_client()

        await self._client.delete(self._otp_key(email=email))  # type: ignore

    # async def otp_exist(self, email: EmailStr) -> bool:
    #     self._ensure_client()
    
    #     return await self._client.exists(self._otp_key(email)) == 1 # type: ignore
    
    async def get_otp_ttl(self,email:EmailStr) -> int | None:
        self._ensure_client()

        ttl = await self._client.ttl(self._otp_key(email=email)) #type: ignore
    
        if ttl < 0:
            return None
        return ttl
    


# Singletone instance
redis_manager = RedisManager()


#this is made to act as a dependency provider
def get_redis_manager() -> RedisManager:
    return redis_manager
