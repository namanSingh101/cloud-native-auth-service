from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError, SecretStr, EmailStr
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):

    # api settings
    API_PREFIX: str = Field(
        default="/api",
        description="Global api prefix"
    )

    # CORS settings
    CORS_ALLOW_ORIGINS: List[str] = Field(
        default_factory=list,
        description="Allowed CORS origins"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default_factory=lambda: ["*"]
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default_factory=lambda: ["*"]
    )
    CORS_ALLOW_CREDENTIALS: bool = True

    # db settings
    DB_USER: str = Field(..., description="Database user")
    DB_PASSWORD: str = Field(..., description="Database pswd")
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: str = Field(..., description="Database port")
    DB_NAME: str = Field(..., description="Database dbname")
    SSL_MODE: str = Field(default="require", description="Database connection")

    # redis settings
    REDIS_HOST: str = Field(..., description="Redis host")
    REDIS_PORT: str = Field(..., description="Redis port")
    REDIS_DB: int = Field(default=0, description="Type of db")
    REDIS_PSWD: Optional[str] = None
    REDIS_USE_SSL: bool = False

    # rate limiting
    RATE_LIMIT_DEFAULT: str
    RATE_LIMIT_ENABLED: bool

    # auth system
    SECRET_KEY: SecretStr
    ALGO: str = "HS256"
    TOKEN_EXPIRE_MIN: int = 30

    # mail service
    MAIL_USERNAME: EmailStr = Field(..., description="Gmail address")
    MAIL_PASSWORD: SecretStr = Field(..., description="Gmail app password")
    MAIL_FROM: EmailStr = Field(..., description="Sender email address")
    MAIL_FROM_NAME: str = Field(
        default="SMTP", description="Sender display name")
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    MAIL_PORT: int = Field(default=587)
    MAIL_STARTTLS: bool = Field(default=True)
    MAIL_SSL_TLS: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def REDIS_URL(self) -> str:
        scheme = "rediss" if self.REDIS_USE_SSL else "redis"
        if self.REDIS_PSWD:
            return (
                f"{scheme}://:{self.REDIS_PSWD}"
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )

        return (
            f"{scheme}://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore[reportCallIssue]
    except ValidationError as e:
        raise RuntimeError("Failed to load the db variables") from e
