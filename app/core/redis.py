import redis.asyncio as aioredis
from app.core import get_settings,DatabaseError
from redis.asyncio import Redis,ConnectionPool

settings = get_settings()

class RedisManager:

    def __init__(self):   
        self._pool:ConnectionPool | None = None
        self._client: Redis | None = None

    async def init(self):
        """Call once on startup to initialize the pool."""
        self._pool = aioredis.ConnectionPool(
            host = settings.REDIS_HOST,
            port = settings.REDIS_PORT,
            db = settings.REDIS_DB_OTP,
            max_connections=20,
            decode_responses=True
        )
        self._client = aioredis.Redis(connection_pool=self._pool)
        print(type(self._client))

    def get_client(self) -> Redis:
         """Returns a Redis client using the shared pool."""
         if self._client is None:
             raise DatabaseError("Redis DB failed to launch")
         return  self._client       

    # async def ping(self) -> bool:
    #     """Health check — verify connection after init."""
    #     client = self.get_client()
    #     return await client.ping()



# async def get_redis_client() -> aioredis.Redis:
#     return aioredis.Redis(connection_pool=redis_pool)