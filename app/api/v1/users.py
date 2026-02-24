from fastapi import APIRouter, Request, Response, status, Depends, HTTPException,BackgroundTasks
from fastapi_mail import NameEmail
from fastapi_mail.errors import ConnectionErrors
from typing import Annotated
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_


from app.core import get_settings, limiter, get_current_user,hash_password
from app.db import get_db
from app.models import User
from app.services import send_otp_email
from app.utils import generate_otp,hash_otp
from app.schemas import UserPrivateResponse, UserCreate, UserUpdate, ApiResponse


router = APIRouter(prefix="/users", tags=["users"])
settings = get_settings()


"""To get the users details using token."""


@router.get("/me", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True)
@limiter.limit("20/minute")
async def read_me(request: Request, response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:
    """ get currently authenticated user. """

    return ApiResponse(success=True, message="User details", data=UserPrivateResponse.model_validate(current_user))


# """To get user details based on user id"""


# @router.get("/{user_id}", response_model=UserPublicResponse)
# @limiter.limit("5/second")
# async def get_user(request: Request, response: Response, user_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]):
#     result = await db.execute(
#         select(User).where(User.id == user_id)
#     )
#     user = result.scalars().first()
#     if user:
#         return user
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                         detail="User not found")


"""Create new user"""


@router.post("", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_user(request: Request, response: Response, user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:
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

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    await db.flush()   
    await db.refresh(new_user)
    return ApiResponse(success=True, message="New user created successfully!", data=UserPrivateResponse.model_validate(new_user))


"""Update user details"""


@router.patch("/me", response_model=ApiResponse[UserPrivateResponse], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def user_update(request: Request, response: Response, update_payload: UserUpdate, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]) -> ApiResponse[UserPrivateResponse]:

    update_data = update_payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.refresh(current_user)

    return ApiResponse(success=True, message="User update successfully!", data=UserPrivateResponse.model_validate(current_user))

"""Delete user"""


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_user(request: Request, response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):

    await db.delete(current_user)


@router.get("/send-otp", response_model=ApiResponse[None], response_model_exclude_none=True,status_code=status.HTTP_200_OK)
async def send_otp(request: Request, response: Response, background_task: BackgroundTasks) -> ApiResponse[None]:
    try:
        otp = generate_otp()
        hashed_otp = hash_otp(otp=otp)
        email: NameEmail = NameEmail._validate("Naman <naman10jan@gmail.com>")
        background_task.add_task(send_otp_email, email, hashed_otp)

        return ApiResponse(success=True, message="Email sent succesfully")
    except (ConnectionErrors, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending email"
        )
