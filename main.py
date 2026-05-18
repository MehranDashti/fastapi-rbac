from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import RequestLoggingMiddleware
# from app.api.v1.routers import user_router  # uncomment when ready

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        # Hide docs in production
        docs_url=None if settings.PRODUCTION else "/docs",
        redoc_url=None if settings.PRODUCTION else "/redoc",
        openapi_url=None if settings.PRODUCTION else "/openapi.json",
    )

    # --- Middleware (order matters: first added = outermost) ---

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # GZip compression for responses > 1KB
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Request logging (innermost so it wraps the actual handler)
    app.add_middleware(RequestLoggingMiddleware)

    # --- Routers ---
    # app.include_router(user_router.router, prefix="/api/v1")

    # --- Lifecycle events ---
    @app.on_event("startup")
    async def startup():
        logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
        logger.info(f"PRODUCTION={settings.PRODUCTION}, WORKERS={settings.SERVER_WORKERS}")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info(f"{settings.APP_NAME} shutting down")

    # --- Health check ---
    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app

app = create_app()