from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update

from app.core import get_settings, limiter, get_current_user, create_access_token, verify_password, hash_password
from app.db import get_db
from app.models import User
from app.schemas import Token, NewPswdPayload, ApiResponse


router = APIRouter(prefix="/auth", tags=["health"])
settings = get_settings()


@router.post("/login", response_model=ApiResponse[Token], status_code=status.HTTP_200_OK, response_model_exclude_none=True)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ApiResponse[Token]:

    result = await db.execute(
        select(User).where(
            or_(
                User.username == form_data.username.lower(),
                User.email == form_data.username.lower()
            )
        )
    )
    user = result.scalars().first()

    # verify user exists and password is correct
    # don't reveal which one failed

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    # create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.TOKEN_EXPIRE_MIN)
    access_token = create_access_token(
        data={"sub": str(user.id), "token_version": user.token_version},
        expires_delta=access_token_expires
    )
    return ApiResponse(success=True, data=Token(access_token=access_token, token_type="bearer"))


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def change_password(request: Request, response: Response, pswd_payload: NewPswdPayload, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    """Change user password"""
    if not verify_password(pswd_payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect password try again",
                            headers={"WWW-Authenticate": "Bearer"})

    stmt = update(User).where(User.id == current_user.id).values(password_hash=hash_password(
        pswd_payload.new_password), token_version=User.token_version + 1)
    await db.execute(stmt)
