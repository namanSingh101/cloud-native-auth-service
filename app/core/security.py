from datetime import UTC, datetime, timedelta
from pwdlib import PasswordHash
from typing import Optional
import jwt
import uuid
from jwt import InvalidTokenError
import hashlib
import hmac

from app.core import get_settings

settings = get_settings()

# password hasher + argon2 is default sec
password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


#SHA-256 — for tokens (high entropy, needs speed)
def hash_refresh_token(refresh_token:str) -> str:
    return hashlib.sha256(refresh_token.encode()).hexdigest()

def verify_refresh_token(raw_token:str,stored_hash:str) -> bool:
      return hmac.compare_digest(
        hashlib.sha256(raw_token.encode()).hexdigest(),
        stored_hash
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a jwt access token"""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )
    payload = {
        **data,
        "exp":expire,
        "type":"access",
        "iat":datetime.now(UTC)
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGO
    )

    


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """Create a jwt refesh token"""
    jti = str(uuid.uuid4())

    expire = datetime.now(UTC) + (
        expires_delta or timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )
   
    payload = {
        **data,
        "exp":expire,
        "jti":jti,
        "type":"refresh",
        "iat":datetime.now(UTC)
    }

    encoded_refresh_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGO
    )

    return encoded_refresh_jwt, jti


def decode_access_token(token: str) -> dict:
    """Verify a jwt access token and return the subject(user id) if valid"""

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGO],
            options={"require": ["exp", "sub", "token_version"]}
        )

    except InvalidTokenError as e:
        raise InvalidTokenError("Invalid token")
    else:
        return payload
