from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError
from typing import Annotated
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import decode_access_token
from app.db import get_db
from app.models import User
from app.schemas import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_token(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenPayload:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        # Required claims
        sub = payload.get("sub")
        token_version = payload.get("token_version")
        exp = payload.get("exp")

        if not sub or not token_version or not exp:
            raise credentials_exception

          # Validate UUID format
        try:
            UUID(sub)
        except ValueError:
            raise credentials_exception

        return TokenPayload(sub=sub, token_version=token_version, exp=exp)

    except (InvalidTokenError, TypeError, ValueError) as e:
        raise credentials_exception


async def get_current_user(token_payload: Annotated[TokenPayload, Depends(get_current_token)], db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials could not be validated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    result = await db.execute(
        select(User).where(User.id == token_payload.sub),
    )
    user = result.scalars().first()

    if not user:
        raise credentials_exception

    if user.token_version != token_payload.token_version:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    print("token payload", token_payload)
    print("user", user)
    return user
