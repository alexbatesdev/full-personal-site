from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from personal_site_backend.api.router import api_router

app = FastAPI(title="Personal Site Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://static.piinro.place"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def main() -> None:
    uvicorn.run("personal_site_backend.main:app", reload=True)
