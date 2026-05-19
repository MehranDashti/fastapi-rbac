from fastapi import APIRouter

from app.api.v1.routers.client.user_router import router as user_router

router = APIRouter()
router.include_router(user_router)
