from fastapi import APIRouter, Request, Response, status, Depends, HTTPException, BackgroundTasks
from fastapi_mail.errors import ConnectionErrors
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import NameEmail

from app.core import get_settings, limiter, get_current_user, hash_password,get_otp_manager,OTPRedisManager
from app.db import get_db
from app.models import User
from app.services import send_otp_email
from app.utils import generate_otp, hash_otp
from app.schemas import UserPrivateResponse, UserCreate, UserUpdate, ApiResponse


router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


@router.get("/me", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True)
@limiter.limit("20/minute")
async def read_me(request: Request, response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:
    """ get currently authenticated user. """
    """To get the users details using token."""
    print(current_user)
    return ApiResponse(success=True, message="User details", data=UserPrivateResponse.model_validate(current_user))


@router.post("", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_user(request: Request, response: Response, user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:
    """Create new user"""

    result = await db.execute(
        select(User).where(
            or_(
                User.username == user.username.lower(),
                User.email == user.email.lower()
            )
        )
    )

    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    user_data = user.model_dump(exclude_none=True)
    user_data.pop("password")
    new_user = User(
        **user_data,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return ApiResponse(success=True, message="New user created successfully!", data=UserPrivateResponse.model_validate(new_user))


@router.patch("/me", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def user_update(request: Request, response: Response, update_payload: UserUpdate, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:
    """Update user details"""
    update_data = update_payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.refresh(current_user)

    return ApiResponse(success=True, message="User update successfully!", data=UserPrivateResponse.model_validate(current_user))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_user(request: Request, response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete user"""
    await db.delete(current_user)


@router.post("/request-email-otp", response_model=ApiResponse[None], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
async def send_otp(request: Request, response: Response, background_task: BackgroundTasks, current_user: Annotated[User, Depends(get_current_user)], redis: Annotated[OTPRedisManager, Depends(get_otp_manager)]) -> ApiResponse[None]:
    """Email service functionality"""
    ttl = await redis.get_otp_ttl(current_user.email,key_prefix=settings.OTP_KEY_VERIFY)
    "working good "
    if ttl is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"OTP already send. Please wait {ttl} seconds before requesting again.",
            headers={"Retry-After": str(ttl)}
        )

    otp = generate_otp()
    hashed_otp = hash_otp(otp=otp)
    try:
        email: NameEmail = NameEmail(name=current_user.first_name.capitalize(
        ) if current_user.first_name else "User", email=current_user.email)

        # save the hashed otp
        await redis.set_otp(email=email.email, hashed_otp=hashed_otp,key_prefix=settings.OTP_KEY_VERIFY)

        background_task.add_task(send_otp_email, email, otp)

        return ApiResponse(success=True, message="OTP sent succesfully check email!")
    except (ConnectionErrors, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending email"
        )
