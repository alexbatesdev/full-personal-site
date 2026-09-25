from fastapi import APIRouter

from personal_site_backend.api.routes.health import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)