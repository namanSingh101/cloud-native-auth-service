from fastapi import status

class AppException(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class DatabaseError(AppException):

    def __init__(self, message="Database operation failed", details=None):
        super().__init__(
            error_code="DB_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ResourceNotFoundError(AppException):
    def __init__(self, *, resource: str, identifier: str):
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"id": identifier}
        )


class BusinessRuleViolation(AppException):
    def __init__(self,message:str,details=None):
        super().__init__(
            error_code="BUSINESS_RULE_VIOLATION",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details
        )

 