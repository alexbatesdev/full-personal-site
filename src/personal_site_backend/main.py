from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn


from personal_site_backend.api.router import api_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEBSITE_DIRECTORY = PROJECT_ROOT / "src" / "personal_site_imported_frontend"

app = FastAPI(title="Personal Site Backend")

app.include_router(api_router)

app.mount(
    "/",
    StaticFiles(directory=WEBSITE_DIRECTORY, html=True),
    name="website",
)


def main() -> None:
    uvicorn.run("personal_site_backend.main:app", reload=True)
