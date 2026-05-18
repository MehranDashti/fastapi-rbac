from fastapi import APIRouter

from app.api.v1.routers import admin_user_router, client_user_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(client_user_router.router)
api_router.include_router(admin_user_router.router)