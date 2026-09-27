from fastapi import APIRouter

from personal_site_backend.api.routes.health import router as health_router
from personal_site_backend.api.routes.posts import (
    post_html_router,
    post_api_router,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(post_api_router)

html_router = APIRouter(prefix="/html")
html_router.include_router(post_html_router)