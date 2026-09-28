from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import uvicorn

from personal_site_backend.api.router import api_router, html_router

from personal_site_backend.api.dependencies.database import init_db
    
from personal_site_backend.env import WEBSITE_DIRECTORY


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Personal Site Backend", lifespan=lifespan)

app.include_router(api_router)
app.include_router(html_router)

app.mount(
    "/",
    StaticFiles(directory=WEBSITE_DIRECTORY, html=True),
    name="website",
)


def main() -> None:
    uvicorn.run("personal_site_backend.main:app", reload=True)
