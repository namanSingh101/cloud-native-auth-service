from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis
from app.exception_handler import *

from app.core import *

settings = get_settings()

#redis_client = Redis.from_url(settings.REDIS_URL)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    headers_enabled=True,
)


# Global decorator (applies to all routes registered after this)
#global_limit_decorator = limiter.limit(settings.RATE_LIMIT_DEFAULT)
