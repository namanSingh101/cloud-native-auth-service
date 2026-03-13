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
    REDIS_DB_RATE_LIMIT: int = Field(
        default=0, description="Logical seperation for storing rate limiting keys")
    REDIS_DB_OTP: int = Field(default=1, description="For storing hashed otp")
    REDIS_DB_CACHE: int = Field(default=2, description="For cache purpose")
    REDIS_PSWD: Optional[str] = None
    REDIS_USE_SSL: bool = False

    # rate limiting
    RATE_LIMIT_DEFAULT: str
    RATE_LIMIT_ENABLED: bool

    # auth system
    SECRET_KEY: SecretStr
    ALGO: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Access token expire minutes ")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30, description="Refresh token expire days")
    REFRESH_TOKEN_MAX_LIFETIME_DAYS: int = Field(
        default=90, description="Refresh token max expire days")
    # cleanup sessions
    EXPIRED_SESSION_RETENTION_DAYS: int = Field(
        default=7, description="Grace period before cleaning up expired sessions")

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

    # Otp service
    OTP_TTL_SECONDS: int = Field(
        default=300, description="Time for otp to be stored")
    OTP_KEY_VERIFY: str = Field(..., description="user verification key")
    OTP_KEY_LOGIN: str = Field(..., description="user login key")

    # Cache service
    CACHE_TTL_SECONDS: int = Field(
        default=3600, description="Time for cache to be stored")
    CACHE_KEY: str = Field(..., description="cache key")

    # # file handling
    # MAX_FILE_SIZE_MB_AVA: int = 5
    # MAX_FILE_SIZE_MB_DOC: int = 20

    # ALLOWED_CONTENT_TYPES_DOC: dict[str, str] = Field(default={
    #     "application/pdf": ".pdf",
    # }, description="Allowd ext. type for file upload")
    # ALLOWED_CONTENT_TYPES_AVA: dict[str, str] = Field(default={
    #     "image/jpeg": ".jpeg",
    #     "image/png": ".png",
    # }, description="Allowd ext. type for file upload")
    # MAGIC_BYTES: dict[str, bytes] = Field(default={
    #     ".pdf": b"%PDF",
    #     ".jpeg": b"\xff\xd8\xff",
    #     ".png": b"\x89PNG\r\n\x1a\n"
    # }, description="For validation for file type")

    #file upload url expiry  
    #FILE_UPLOAD_EXPIRE:int = Field(...,description="File upload ur expired")
    PRESIGNED_URL_TTL_SECONDS:int = Field(...,description="File upload url TTL in seconds")

    #aws s3 bucket config
    AWS_ACCESS_KEY_ID:str 
    AWS_SECRET_ACCESS_KEY:SecretStr
    AWS_REGION:str
    S3_BUCKET_NAME:str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # @property
    # def MAX_FILE_SIZE_DOC(self) -> int:
    #     return self.MAX_FILE_SIZE_DOC*1024*1024

    # @property
    # def MAX_FILE_SIZE_AVA(self) -> int:
    #     return self.MAX_FILE_SIZE_MB_AVA*1024*1024

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
                f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_RATE_LIMIT}"
            )

        return (
            f"{scheme}://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_RATE_LIMIT}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()  # type: ignore[reportCallIssue]
    except ValidationError as e:
        raise RuntimeError("Failed to load the db variables") from e
