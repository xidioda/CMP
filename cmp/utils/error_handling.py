"""
Enhanced Error Handling System for CMP

Provides comprehensive error handling, validation, and user-friendly responses
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
import traceback
import time
from datetime import datetime

# Avoid circular import by importing logger conditionally
def get_logger(name: str):
    try:
        from ..logging_config import get_logger as _get_logger
        return _get_logger(name)
    except ImportError:
        import logging
        return logging.getLogger(name)

logger = get_logger("error_handler")


class ErrorCode(str, Enum):
    """Standardized error codes for the CMP platform"""
    
    # Authentication & Authorization
    INVALID_CREDENTIALS = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    TOKEN_INVALID = "AUTH_003"
    INSUFFICIENT_PERMISSIONS = "AUTH_004"
    USER_NOT_FOUND = "AUTH_005"
    USER_INACTIVE = "AUTH_006"
    
    # Validation Errors
    INVALID_INPUT = "VAL_001"
    MISSING_REQUIRED_FIELD = "VAL_002"
    INVALID_EMAIL_FORMAT = "VAL_003"
    INVALID_PASSWORD_FORMAT = "VAL_004"
    INVALID_AMOUNT_FORMAT = "VAL_005"
    INVALID_DATE_FORMAT = "VAL_006"
    
    # Business Logic Errors
    TRANSACTION_NOT_FOUND = "BIZ_001"
    INVOICE_PROCESSING_FAILED = "BIZ_002"
    BANK_INTEGRATION_ERROR = "BIZ_003"
    ZOHO_API_ERROR = "BIZ_004"
    AI_PROCESSING_ERROR = "BIZ_005"
    OCR_PROCESSING_ERROR = "BIZ_006"
    
    # System Errors
    DATABASE_ERROR = "SYS_001"
    EXTERNAL_API_ERROR = "SYS_002"
    FILE_UPLOAD_ERROR = "SYS_003"
    INTERNAL_SERVER_ERROR = "SYS_004"
    SERVICE_UNAVAILABLE = "SYS_005"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_001"
    
    # Resource Errors
    RESOURCE_NOT_FOUND = "RES_001"
    RESOURCE_CONFLICT = "RES_002"
    RESOURCE_QUOTA_EXCEEDED = "RES_003"


class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class CMPError(BaseModel):
    """Standardized error response model"""
    success: bool = False
    error_code: ErrorCode
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None
    support_info: Optional[Dict[str, str]] = None


class CMPException(Exception):
    """Base exception class for CMP-specific errors"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        status_code: int = 400,
        context: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or []
        self.status_code = status_code
        self.context = context or {}
        super().__init__(message)


class ValidationException(CMPException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[List[ErrorDetail]] = None):
        if field and not details:
            details = [ErrorDetail(field=field, message=message, code=ErrorCode.INVALID_INPUT)]
        super().__init__(
            error_code=ErrorCode.INVALID_INPUT,
            message=message,
            details=details,
            status_code=422
        )


class AuthenticationException(CMPException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed", error_code: ErrorCode = ErrorCode.INVALID_CREDENTIALS):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=401
        )


class AuthorizationException(CMPException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            message=message,
            status_code=403
        )


class BusinessLogicException(CMPException):
    """Exception for business logic errors"""
    
    def __init__(self, error_code: ErrorCode, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=400,
            context=context
        )


class SystemException(CMPException):
    """Exception for system-level errors"""
    
    def __init__(self, error_code: ErrorCode, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=500,
            context=context
        )


def create_error_response(
    error_code: ErrorCode,
    message: str,
    status_code: int = 400,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response"""
    
    error_response = CMPError(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id,
        support_info={
            "documentation": "https://github.com/xidioda/CMP/blob/main/README.md",
            "contact": "For support, create an issue on GitHub"
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    details = []
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_type = error["type"]
        
        # Map Pydantic error types to our error codes
        error_code = ErrorCode.INVALID_INPUT
        if "missing" in error_type:
            error_code = ErrorCode.MISSING_REQUIRED_FIELD
        elif "email" in error_type:
            error_code = ErrorCode.INVALID_EMAIL_FORMAT
        elif "type_error.float" in error_type or "type_error.integer" in error_type:
            error_code = ErrorCode.INVALID_AMOUNT_FORMAT
        
        details.append(ErrorDetail(
            field=field,
            message=message,
            code=error_code,
            context={"pydantic_type": error_type}
        ))
    
    logger.warning(f"Validation error: {exc.errors()}")
    
    return create_error_response(
        error_code=ErrorCode.INVALID_INPUT,
        message="Invalid input provided",
        status_code=422,
        details=details
    )


async def cmp_exception_handler(request: Request, exc: CMPException) -> JSONResponse:
    """Handle CMP-specific exceptions"""
    logger.error(f"CMP Exception: {exc.error_code} - {exc.message}")
    
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = f"req_{int(time.time())}"
    
    logger.error(f"Unhandled exception [{request_id}]: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Don't expose internal error details in production
    return create_error_response(
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="An internal server error occurred",
        status_code=500,
        request_id=request_id
    )


def validate_email(email: str) -> str:
    """Validate email format"""
    import re
    
    if not email:
        raise ValidationException("Email is required", field="email")
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationException("Invalid email format", field="email")
    
    return email.lower().strip()


def validate_password(password: str) -> str:
    """Validate password strength"""
    if not password:
        raise ValidationException("Password is required", field="password")
    
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long", field="password")
    
    if len(password) > 128:
        raise ValidationException("Password must be less than 128 characters", field="password")
    
    return password


def validate_amount(amount: float, field_name: str = "amount") -> float:
    """Validate monetary amounts"""
    if amount is None:
        raise ValidationException(f"{field_name} is required", field=field_name)
    
    if not isinstance(amount, (int, float)):
        raise ValidationException(f"{field_name} must be a number", field=field_name)
    
    if amount < 0:
        raise ValidationException(f"{field_name} cannot be negative", field=field_name)
    
    if amount > 999999999.99:  # 1 billion limit
        raise ValidationException(f"{field_name} cannot exceed 999,999,999.99", field=field_name)
    
    return round(float(amount), 2)


def validate_required_string(value: str, field_name: str, max_length: int = 255) -> str:
    """Validate required string fields"""
    if not value or not value.strip():
        raise ValidationException(f"{field_name} is required", field=field_name)
    
    value = value.strip()
    
    if len(value) > max_length:
        raise ValidationException(f"{field_name} must be less than {max_length} characters", field=field_name)
    
    return value


# Success response model
class SuccessResponse(BaseModel):
    """Standardized success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> SuccessResponse:
    """Create a standardized success response"""
    return SuccessResponse(message=message, data=data)