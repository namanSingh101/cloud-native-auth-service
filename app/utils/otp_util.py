import secrets
import string
import hmac
import hashlib
from pydantic import EmailStr

from app.core import get_settings

settings = get_settings()


def generate_otp(length: int = 6) -> str:
    """
   Generates a cryptographically secure random numeric OTP.
   Default length is 6 digits.
   """

    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp:str) -> str:
    """HMAC-SHA256 hash using app's secret key as salt.Safe to store in redis."""

    return hmac.new(
        key=settings.SECRET_KEY.get_secret_value().encode(),
        msg=otp.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

def verify_otp(plain_otp:str,hashed_otp:str) -> bool:
    return hmac.compare_digest(hash_otp(plain_otp),hashed_otp)

def build_otp_key(email:EmailStr) -> str:
    return f"{settings.OTP_KEY_PREFIX}{email}"