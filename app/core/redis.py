from __future__ import annotations
from typing import Any, Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from pydantic import EmailStr
from abc import ABC, abstractmethod
from enum import Enum

from app.core.config import get_settings
from app.core.global_error import DatabaseError

settings = get_settings()


class RedisStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"


class BaseRedisManager(ABC):
    # we have used "RedisManager" because there is not RedisManager instance type before the class is defined
    # to avoid the "RedisManager" string quotation we can use from __future__ import annotations
    # This makes all annotations in the file lazy (evaluated as strings automatically), so you never need quotes for forward references again

    def __init__(self) -> None:
        # if  _initialized is not used then every time we call for object it will set all variables with none
        # to avoid this during first time when instance is created we set the _initialized = True

        # extending this class for cache purpose also
        # if not hasattr(self,"_initialized"):
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
        self._status: RedisStatus = RedisStatus.DISCONNECTED
        #  self._initialized = True

    # ── Abstract contract ──────────────────────
    @property
    @abstractmethod
    def db_index(self) -> int:
        pass

    # ── Public state ──────────────────────────────────────────────────────────

    @property
    def status(self) -> RedisStatus:
        return self._status

    @property
    def is_available(self) -> bool:
        return self._status == RedisStatus.CONNECTED

    # ── Lifecycle ──────────────────────────────
    async def init(self) -> None:
        try:
            """Call once on startup to initialize the pool."""
            self._pool = self._pool = aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PSWD,
                db=self.db_index,
                max_connections=20,
                decode_responses=True,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            await self.ping()
            self._status = RedisStatus.CONNECTED
        except Exception as e:
            self._status = RedisStatus.DEGRADED
            # raise DatabaseError(f"Redis ping failed: {self.db_index} : {e}")

    async def close(self):
        try:
            """Close pool on shutdown"""
            if self._client:
                await self._client.aclose()
            if self._pool:
                await self._pool.aclose()
        except Exception as e:
            self._status = RedisStatus.DEGRADED
            # raise DatabaseError(f"Redis closing failed: {self.db_index} : {e}")
        finally:
            self._status = RedisStatus.DISCONNECTED
            self._client = None
            self._pool = None
    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def ping(self) -> bool:
        self._ensure_client()
        try:
            result = bool(await self._client.ping())  # type: ignore
            self._status = RedisStatus.CONNECTED if result else RedisStatus.DEGRADED
            return result
        except Exception as e:
            self._status = RedisStatus.DEGRADED
            return False
            # raise DatabaseError(f"Redis ping failed: {self.db_index} : {e}")

    def get_client(self) -> Redis:
        """Returns a Redis client using the shared pool."""
        self._ensure_client()
        return self._client if self.is_available else None  # type: ignore

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _ensure_client(self):
        """Raise early if Redis was never initialized."""
        if self._client is None:
            raise DatabaseError(
                f"{self.__class__.__name__} is not initialized"
                "Redis is not initialized. Call await redis_manager.init() on startup.")


class OTPRedisManager(BaseRedisManager):
    # _instance = None

    @property
    def db_index(self) -> int:
        return settings.REDIS_DB_OTP  # 1

    def _otp_key(self, email: EmailStr, key_prefix: str) -> str:
        return f"{key_prefix}{email}"

    # -------------------------------------------------------------------------
    # OTP operations
    # -------------------------------------------------------------------------

    async def set_otp(self, email: EmailStr, key_prefix: str, hashed_otp: str, ttl: int = settings.OTP_TTL_SECONDS) -> None:
        self._ensure_client()

        # type: ignore
        await self._client.set(self._otp_key(email=email, key_prefix=key_prefix), hashed_otp, ex=ttl) # type: ignore

    async def get_otp(self, email: EmailStr, key_prefix: str) -> Optional[str]:
        self._ensure_client()

        # type: ignore
        return await self._client.get(self._otp_key(email=email, key_prefix=key_prefix))  # type: ignore

    async def delete_otp(self, email: EmailStr, key_prefix: str):
        self._ensure_client()

        # type: ignore
        await self._client.delete(self._otp_key(email=email, key_prefix=key_prefix)) # type: ignore

    # async def otp_exist(self, email: EmailStr) -> bool:
    #     self._ensure_client()

    #     return await self._client.exists(self._otp_key(email)) == 1 # type: ignore

    async def get_otp_ttl(self, email: EmailStr, key_prefix: str) -> Optional[int]:
        self._ensure_client()

        # type: ignore
        ttl = await self._client.ttl(self._otp_key(email=email, key_prefix=key_prefix)) # type: ignore

        if ttl < 0:
            return None
        return ttl


class CacheRedisManager(BaseRedisManager):
    @property
    def db_index(self) -> int:
        return settings.REDIS_DB_CACHE  # 2

    def _cache_key(self, resource: str, identifier_prefix: str) -> str:
        return f"{settings.CACHE_KEY}:{resource}:{identifier_prefix}"

    # -------------------------------------------------------------------------
    # Cache operations
    # -------------------------------------------------------------------------

    async def set_cache(self, resource: str, identifier_prefix: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> None:
        self._ensure_client()

        # type: ignore
        await self._client.set(self._cache_key(resource=resource, identifier_prefix=identifier_prefix), value=value, ex=ttl) # type: ignore

    async def get_cache(self, resource: str, identifier_prefix: str) -> Optional[str]:
        self._ensure_client()

        # type: ignore
        return await self._client.get(self._cache_key(resource=resource, identifier_prefix=identifier_prefix)) # type: ignore

    async def delete_cache(self, resource: str, identifier_prefix: str):
        self._ensure_client()

        # type: ignore
        await self._client.delete(self._cache_key(resource=resource, identifier_prefix=identifier_prefix)) # type: ignore

    async def cache_exist(self, resource: str, identifier_prefix: str) -> bool:
        self._ensure_client()

        # type: ignore
        return await self._client.exists(self._cache_key(resource=resource, identifier_prefix=identifier_prefix)) == 1 # type: ignore


class RedisManager:
    """
    Thin facade that owns both sub-managers and drives their lifecycle.
    Single entry-point for the application.
    """

    def __init__(self) -> None:
        self.otp: OTPRedisManager = OTPRedisManager()
        self.cache: CacheRedisManager = CacheRedisManager()

    async def init(self) -> None:
        await self.otp.init()
        await self.cache.init()

    async def close(self) -> None:
        await self.otp.close()
        await self.cache.close()

    async def ping_all(self) -> dict[str, bool]:
        return {
            "otp_db": await self.otp.ping(),
            "cache_db": await self.cache.ping()
        }

    @property
    def health(self) -> dict:
        return {
            "availability": self.otp.is_available and self.cache.is_available,
            "otp_db":   {"status": self.otp.status.value,   "available": self.otp.is_available},
            "cache_db": {"status": self.cache.status.value, "available": self.cache.is_available},
        }


# Singletone instance
redis_manager = RedisManager()


# this is made to act as a dependency provider
def get_redis_manager() -> RedisManager:
    return redis_manager


def get_otp_manager() -> OTPRedisManager:
    print("email", isinstance(redis_manager.otp, OTPRedisManager))
    return redis_manager.otp


def get_cache_manager() -> CacheRedisManager:
    print("cache", isinstance(redis_manager.cache, OTPRedisManager))
    return redis_manager.cache
