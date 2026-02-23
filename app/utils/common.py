import re
from pydantic.functional_validators import AfterValidator
from typing import Annotated
from app.core import BusinessRuleViolation

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])"
    r"(?=.*[A-Z])"
    r"(?=.*\d)"
    r"(?=.*[@$!%*?&^#()_\-+=])"
    r"[A-Za-z\d@$!%*?&^#()_\-+=]{8,128}$"
)


def validate_password_strength(value: str) -> str:
    if not PASSWORD_REGEX.match(value):
        raise BusinessRuleViolation(
            message="Password must be 8-128 characters and contain uppercase, lowercase, digit, and special character."
        )
    return value


def validate_phone_number(phone: str) -> str:
    """
    Validates international phone numbers.
    Rules:
    - Optional leading +
    - No leading zero after +
    - Total digits: 10 to 15
    - Digits only (no spaces, dashes, brackets)
    """

    if not isinstance(phone, str):
        raise BusinessRuleViolation("Phone number must be a string")

    phone = phone.strip()

    pattern = r"^\+[1-9]\d{9,14}$"

    if not re.fullmatch(pattern, phone):
        raise BusinessRuleViolation(
            "Invalid phone number format. "
            "Must contain 10-15 digits and may start with '+'."
        )

    return phone

PhoneNumber = Annotated[str, AfterValidator(validate_phone_number)]
StrongPassword = Annotated[str, AfterValidator(validate_password_strength)]