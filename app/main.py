from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import APP_NAME, APP_VERSION, GENERATED_DIR, SESSION_SECRET, STATIC_DIR, UPLOAD_DIR
from app.middleware.session import SignedCookieSessionMiddleware
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.services.image_composer import get_cjk_font_path

app = FastAPI(title=APP_NAME)
app.add_middleware(SignedCookieSessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(auth_router)
app.include_router(pages_router)


@app.get("/health")
async def health() -> dict:
    font_path = get_cjk_font_path()
    return {
        "status": "ok",
        "app": "zhongcaoji",
        "version": APP_VERSION,
        "uploads_dir_exists": UPLOAD_DIR.exists(),
        "generated_dir_exists": GENERATED_DIR.exists(),
        "static_dir_exists": STATIC_DIR.exists(),
        "css_file_exists": (STATIC_DIR / "css" / "style.css").exists(),
        "js_file_exists": (STATIC_DIR / "js" / "app.js").exists(),
        "font_file_exists": font_path is not None,
        "font_path": str(font_path) if font_path else None,
    }
