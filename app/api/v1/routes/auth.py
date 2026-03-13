from fastapi import APIRouter, Request, Response, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta, datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload
import uuid
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.core.config import get_settings
from app.core.rate_limiter import limiter 
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password, hash_password, create_refresh_token, hash_refresh_token, decode_access_token
from app.db import get_db
from app.models import User, RefreshSession
from app.schemas import Token, NewPswdPayload, ApiResponse, RefreshTokenRequest
from app.utils import get_ip_address


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

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Account is disabled",
                            )

    # user details
    device_info = request.headers.get("User-Agent", "unknown")
    ip_address = get_ip_address(request)

    # token creation
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_absolute_expire = timedelta(days=settings.REFRESH_TOKEN_MAX_LIFETIME_DAYS)
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {"sub": str(user.id), "token_version": user.token_version}

    # create refresh token with user id as subject
    refresh_token, session_id = create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    # create access token with user id as subject
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )

    refresh_session = RefreshSession(
        id=uuid.UUID(session_id),
        user_id=user.id,
        hashed_token=hash_refresh_token(refresh_token),
        device_info=device_info,
        ip_address=ip_address,
        absolute_expires_at=datetime.now(UTC)+refresh_token_absolute_expire,
        expires_at=datetime.now(UTC) + refresh_token_expires
    )
    db.add(refresh_session)
    await db.flush()

    # Set refresh token as httpOnly cookie (prevents XSS theft)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,          # JS cannot access this
        secure=True,            # HTTPS only
        samesite="lax",         # CSRF protection
        max_age=int(refresh_token_expires.total_seconds()),
        path="/api/v1/auth",    # scoped: only sent to refresh endpoint
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


@router.post("/refresh", response_model=ApiResponse[Token], status_code=status.HTTP_202_ACCEPTED, response_model_exclude_none=True)
@limiter.limit("5/minute")
async def refresh_access_token(request: Request, response: Response,db: Annotated[AsyncSession, Depends(get_db)]):

    credentials_exception = lambda detail : HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail or "Invalid or expired token",
    )
    
    refresh_token = request.cookies.get("refresh_token")
    print("this is refresh token",refresh_token)
  
    if not refresh_token:
        raise credentials_exception("Refresh token missing")

    try:
        payload = decode_access_token(refresh_token)
    except ExpiredSignatureError:
        raise credentials_exception("Refresh token expired")
    except (InvalidTokenError, TypeError, ValueError) as e:
        raise credentials_exception("Refresh token expired 1")
    print("this is payload",payload)
    

    if payload.get("type") != "refresh":
        raise credentials_exception("Invalid token type")
    
    # type:ignore[reportAssignmentType]
    user_id: str | None = payload.get("sub")
    # type:ignore[reportAssignmentType]
    session_id: str | None = payload.get("jti")
    if not user_id or not session_id:
        raise credentials_exception("Invalid token payload")
    
    #check user id  matchs with the current user getting from access token
    # if current_user.id != uuid.UUID(user_id):
    #     raise credentials_exception("Access token is invalid") 

    smt = select(RefreshSession).where(RefreshSession.id == uuid.UUID(session_id)).options(
        selectinload(RefreshSession.user))  # avoid lazy load on async session
    result = await db.execute(smt)
    # session details
    session: RefreshSession | None = result.scalars().first()

    
    if not session:
        raise credentials_exception("Session not found")
    
    if session.is_revoked:
        if session.replaced_by_token_id is not None:
            # Token is rotated but reused - this is theft
            await db.execute(
                update(RefreshSession)
                .where(
                    RefreshSession.user_id == session.user_id,
                    RefreshSession.is_revoked == False,
                )
                .values(is_revoked=True)
            )
            await db.commit()
            raise credentials_exception(
                "Token reuse detected — all sessions revoked")
        else:
            raise credentials_exception("Session has been revoked")
    
    # current date
    now = datetime.now(UTC)
    # check for session expire
    if session.expires_at.replace(tzinfo=UTC) < now:
        session.is_revoked = True
        await db.commit()
        raise credentials_exception("Session expired please login again")

    if session.absolute_expires_at.replace(tzinfo=UTC) < now:
        session.is_revoked = True
        await db.commit()
        raise credentials_exception(
            "Maximum session lifetime reached, please login again")

    if str(session.user_id) != user_id:
        raise credentials_exception("User mismatch")

    if hash_refresh_token(refresh_token) != session.hashed_token:
        raise credentials_exception("Token mismatch")
    
    # check wether the account is still active
    user: User = session.user
    if not user.is_active:
        raise credentials_exception("Account is disabled")
  
    # check wether the user has not changed the password
    if payload.get("token_version") != user.token_version:
        raise credentials_exception(
            "Token has been invalidated - please login again")

    # new access token created
    new_access_token = create_access_token(
        data={"sub": str(user.id), "token_version": user.token_version},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # user details
    device_info = request.headers.get("User-Agent", "unknown")
    ip_address = get_ip_address(request)

    # token creation
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token, new_session_id = create_refresh_token(
        data={"sub": str(user.id), "token_version": user.token_version},
        expires_delta=refresh_token_expires
    )

    new_refresh_session = RefreshSession(
        id=uuid.UUID(new_session_id),
        user_id=user.id,
        hashed_token=hash_refresh_token(new_refresh_token),
        device_info=device_info,
        ip_address=ip_address,
        expires_at=datetime.now(UTC) + refresh_token_expires,
        absolute_expires_at=session.absolute_expires_at,
    )
    db.add(new_refresh_session)
    await db.flush()
    await db.refresh(new_refresh_session)

    await db.execute(
        update(RefreshSession)
        .where(RefreshSession.id == session.id)
        .values(
            is_revoked=True,
            replaced_by_token_id=new_refresh_session.id
        )
    )
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds()),
        path="/api/v1/auth",
    )

    return ApiResponse(success=True, data=Token(access_token=new_access_token, token_type="bearer"))
