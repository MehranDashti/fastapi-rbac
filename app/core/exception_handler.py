from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

_ERROR_MESSAGES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthenticated",
    403: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Validation Exception",
    500: "Unexpected Exception",
}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = _ERROR_MESSAGES.get(exc.status_code, "Something went wrong")
    content = {
        "success": False,
        "code": exc.status_code,
        "message": message,
        "error": {"detail": exc.detail},
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: dict[str, list[str]] = {}
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.setdefault(field, []).append(err["msg"])
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": 422,
            "message": "Validation Exception",
            "error": errors,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": 500,
            "message": "Unexpected Exception",
            "error": {"detail": "An unexpected error occurred."},
        },
    )
