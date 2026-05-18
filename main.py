from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"PRODUCTION={settings.PRODUCTION}  WORKERS={settings.SERVER_WORKERS}")

    # Import models so Alembic / Base.metadata knows about them
    import app.models.user 

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info(f"{settings.APP_NAME} shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url=None if settings.PRODUCTION else "/docs",
        redoc_url=None if settings.PRODUCTION else "/redoc",
        openapi_url=None if settings.PRODUCTION else "/openapi.json",
    )

    # ── Middleware (outermost first) ───────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(RequestLoggingMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── System routes ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()