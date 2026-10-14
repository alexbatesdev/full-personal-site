import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from personal_site_backend.api.dependencies.database import init_db
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from personal_site_backend.api.router import api_router, html_router
from personal_site_backend.env import WEBSITE_DIRECTORY

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Personal Site Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://static.piinro.place"],
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(api_router)
app.include_router(html_router)

if os.environ.get("PERSONAL_SITE_SERVE_FRONTEND") == "1":
    app.mount(
        "/",
        StaticFiles(directory=WEBSITE_DIRECTORY, html=True),
        name="website",
    )


def main() -> None:
    uvicorn.run("personal_site_backend.main:app", reload=True)
