from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_role_permission import init_rbac, PermissionConfig

from app.core.config import settings
from app.core.exception_handler import (
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.response import ok
from app.db.session import create_tables, get_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await create_tables()
    yield


def create_app() -> FastAPI:
    from app.core.dependencies import get_current_user
    from app.models.user import User

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.PRODUCTION else None,
        redoc_url="/redoc" if not settings.PRODUCTION else None,
        openapi_url="/openapi.json" if not settings.PRODUCTION else None,
        lifespan=lifespan,
    )

    # Must be called before importing routers: require_permission() reads _state at
    # module-load time (as a default argument), so init_rbac must run first.
    init_rbac(
        app,
        get_db=get_db,
        get_current_user=get_current_user,
        user_model=User,
        config=PermissionConfig(guard_name="api"),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    from app.api.v1.router import api_router
    app.include_router(api_router)

    @app.get("/health", tags=["Health"], include_in_schema=not settings.PRODUCTION)
    async def health():
        return ok({"status": "ok", "version": settings.APP_VERSION})

    return app


app = create_app()
