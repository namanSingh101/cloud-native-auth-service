from datetime import UTC,datetime,timedelta
from pwdlib import PasswordHash
from typing import Optional
import jwt
from jwt import InvalidTokenError

from app.core import get_settings

settings = get_settings()

#password hasher + argon2 is default sec 
password_hasher = PasswordHash.recommended()

def hash_password(password:str) -> str:
    return password_hasher.hash(password)

def verify_password(password:str,hashed_password:str) -> bool:
    return password_hasher.verify(password,hashed_password)


def create_access_token(data:dict,expires_delta:Optional[timedelta] = None) -> str:
    """Create a jwt access token"""

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.TOKEN_EXPIRE_MIN
        )
    to_encode.update({"exp":expire})
    #to_encode.update({"type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGO
    )

    return encoded_jwt

def decode_access_token(token:str) -> dict:
    """Verify a jwt access token and return the subject(user id) if valid"""

    try:
       
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGO],
            options={"require":["exp","sub","token_version"]}
        )
        
    except InvalidTokenError as e:
        raise InvalidTokenError("Invalid token")
    else:
        return payload

    