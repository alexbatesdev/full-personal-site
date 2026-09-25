from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn


from personal_site_backend.api.router import api_router

WEBSITE_DIRECTORY = Path(
    r"C:\Users\Alex\Documents\My_Documents__\Personal Code\neocity-website"
)

app = FastAPI(title="Personal Site Backend")

app.include_router(api_router)

app.mount(
    "/",
    StaticFiles(directory=WEBSITE_DIRECTORY, html=True),
    name="website",
)


def main() -> None:
    uvicorn.run("personal_site_backend.main:app", reload=True)
