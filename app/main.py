from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_NAME, APP_VERSION, GENERATED_DIR, STATIC_DIR, UPLOAD_DIR
from app.routes.pages import router as pages_router

app = FastAPI(title=APP_NAME)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(pages_router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": "zhongcaoji",
        "version": APP_VERSION,
        "uploads_dir_exists": UPLOAD_DIR.exists(),
        "generated_dir_exists": GENERATED_DIR.exists(),
    }
