from fastapi import APIRouter

from app.api.v1.routers.admin.user_router import router as user_router
from app.api.v1.routers.admin.role_router import router as role_router
from app.api.v1.routers.admin.permission_router import router as permission_router

router = APIRouter()
router.include_router(user_router)
router.include_router(role_router)
router.include_router(permission_router)
