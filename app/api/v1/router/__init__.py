from fastapi import APIRouter
 
from app.api.v1.routers.client_user_router import router as auth_router
from app.api.v1.routers.admin_user_router import router as admin_user_router
from app.api.v1.routers.role_router import router as role_router
from app.api.v1.routers.permission_router import router as permission_router
 
api_router = APIRouter(prefix="/api/v1")
 
# ── public / client auth ──────────────────────────────────────────────────────
api_router.include_router(auth_router)
 
# ── admin ─────────────────────────────────────────────────────────────────────
api_router.include_router(admin_user_router,  prefix="/admin")
api_router.include_router(role_router,        prefix="/admin")
api_router.include_router(permission_router,  prefix="/admin")
 