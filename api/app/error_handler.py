from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from datetime import datetime
from .log_stream import log


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed logging."""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    log(f"[VALIDATION ERROR] {request.method} {request.url.path}")
    log(f"[VALIDATION ERROR] Details: {error_details}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": error_details
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with logging."""
    log(f"[HTTP ERROR {exc.status_code}] {request.method} {request.url.path}")
    log(f"[HTTP ERROR] {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with full logging."""
    error_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    log(f"[CRITICAL ERROR {error_id}] {request.method} {request.url.path}")
    log(f"[CRITICAL ERROR {error_id}] {type(exc).__name__}: {str(exc)}")
    log(f"[CRITICAL ERROR {error_id}] Traceback:")
    for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
        log(f"[CRITICAL ERROR {error_id}] {line.strip()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "error_id": error_id,
            "message": "An unexpected error occurred. Please check the logs."
        }
    )


def setup_exception_handlers(app):
    """Register all exception handlers."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)