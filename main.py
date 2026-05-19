from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.db.session import create_tables, drop_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await create_tables()
    yield
    # nothing to tear down for now (connection pool closes itself)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if not settings.PRODUCTION else None,
        redoc_url="/redoc" if not settings.PRODUCTION else None,
        openapi_url="/openapi.json" if not settings.PRODUCTION else None,
        lifespan=lifespan,
    )

    # ── middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # ── routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── health ────────────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], include_in_schema=not settings.PRODUCTION)
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()