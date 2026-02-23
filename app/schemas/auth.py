from pydantic import BaseModel, Field, field_validator,model_validator
from typing import Literal, Annotated
from app.utils import StrongPassword
from app.core import BusinessRuleViolation


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class TokenPayload(BaseModel):
    sub: str
    token_version: int
    exp: int


class NewPswdPayload(BaseModel):
    current_password: str = Field(min_length=8, max_length=20)
    new_password: StrongPassword
    confirm_password: StrongPassword

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise BusinessRuleViolation("Passwords do not match")
        if self.current_password == self.new_password:
            raise BusinessRuleViolation("New password must differ from current password")
        return self



