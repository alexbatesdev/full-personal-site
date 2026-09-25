from fastapi import FastAPI
import uvicorn

from personal_site_backend.api.router import api_router

app = FastAPI(title="Personal Site Backend")

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

def main() -> None:
	uvicorn.run("personal_site_backend.main:app", reload=True)