"""Application exception hierarchy and centralized exception handlers.

Mirrors Medicare's WebResponseUtils.fromException() approach — all exceptions
produce a consistent {message, data} JSON envelope.
"""

from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# Base Exception
# ---------------------------------------------------------------------------

class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Specific Exceptions
# ---------------------------------------------------------------------------

class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND", details=details)


class BadRequestException(AppException):
    """Bad request."""

    def __init__(self, message: str = "Bad request", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=400, error_code="BAD_REQUEST", details=details)


class UnauthorizedException(AppException):
    """Unauthorized."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED", details=details)


class ForbiddenException(AppException):
    """Forbidden."""

    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN", details=details)


class ConflictException(AppException):
    """Conflict."""

    def __init__(self, message: str = "Conflict", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=409, error_code="CONFLICT", details=details)


class ValidationException(AppException):
    """Custom validation error."""

    def __init__(self, message: str = "Validation error", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR", details=details)


class ExternalServiceException(AppException):
    """External service failure."""

    def __init__(self, message: str = "External service error", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=502, error_code="EXTERNAL_SERVICE_ERROR", details=details)


class InvalidStateTransitionException(AppException):
    """Invalid status transition."""

    def __init__(self, message: str = "Invalid state transition", details: Optional[Any] = None) -> None:
        super().__init__(message=message, status_code=422, error_code="INVALID_STATE_TRANSITION", details=details)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

def _error_response(
    status_code: int,
    message: str,
    error_code: str = "ERROR",
    details: Optional[Any] = None,
) -> JSONResponse:
    """Build consistent error envelope matching Medicare's {message, data} pattern."""
    body: dict[str, Any] = {
        "message": message,
        "data": None,
    }
    if details is not None:
        body["errors"] = details
    if error_code:
        body["error_code"] = error_code
    return JSONResponse(status_code=status_code, content=body)


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
    )


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code=f"HTTP_{exc.status_code}",
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status_code=422,
        message="Validation error",
        error_code="VALIDATION_ERROR",
        details=jsonable_encoder(
            exc.errors(),
            custom_encoder={Exception: str, ValueError: str},
        ),
    )


async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Never leak stack traces to clients
    return _error_response(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
