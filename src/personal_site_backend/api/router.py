from fastapi import APIRouter

from personal_site_backend.api.routes.health import router as health_router
from personal_site_backend.api.routes.posts import router as posts_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(posts_router) 