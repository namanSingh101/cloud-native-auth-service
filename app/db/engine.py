from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession,AsyncEngine

from app.core import get_settings

settings = get_settings()

engine:AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=True,
    future=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "statement_cache_size": 0,  #for PgBouncer transaction mode
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False
)