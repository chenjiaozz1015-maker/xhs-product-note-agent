from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
GENERATED_DIR = STATIC_DIR / "generated"
TEMPLATE_ASSETS_DIR = STATIC_DIR / "template_assets"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = os.getenv("APP_NAME", "种草机")
APP_TITLE = os.getenv("APP_TITLE", APP_NAME)
APP_VERSION = os.getenv("APP_VERSION", "v0.1-5")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
