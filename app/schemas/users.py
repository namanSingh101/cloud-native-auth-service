from pydantic import BaseModel, ConfigDict, Field, EmailStr,model_validator
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional,Annotated

from app.core import BusinessRuleViolation
from app.utils import StrongPassword,PhoneNumber

Name = Annotated[str,Field(min_length=2,max_length=50)]

class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=120)
    model_config = ConfigDict(str_strip_whitespace=True)


class UserCreate(UserBase):
    password: StrongPassword
    first_name: Optional[Name] = None
    last_name: Optional[Name] = None
    phone_number:Optional[PhoneNumber] = None
    role: UserRole = UserRole.user
    is_verified:Optional[bool] = False



class UserUpdate(BaseModel):
    first_name:Optional[Name] = None
    last_name:Optional[Name] = None
    phone_number:Optional[PhoneNumber] = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls,values):
        if not any(values.values()):
            raise BusinessRuleViolation("Unauthorised update","Empty update found please provide at least one field")
        return values

class UserPublicResponse(BaseModel):
    # Identity and core info
    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserPrivateResponse(UserPublicResponse):
    first_name: Optional[Name] = None
    last_name: Optional[Name] = None
    email: EmailStr

    # status
    is_active: bool
    role: UserRole = UserRole.user

    # Timestamp
    created_at: datetime
