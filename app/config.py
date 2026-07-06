from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
GENERATED_DIR = STATIC_DIR / "generated"
TEMPLATE_ASSETS_DIR = STATIC_DIR / "template_assets"
FONTS_DIR = STATIC_DIR / "fonts"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = os.getenv("APP_NAME", "种草机")
APP_TITLE = os.getenv("APP_TITLE", APP_NAME)
APP_VERSION = os.getenv("APP_VERSION", "v0.5-2")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-session-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/zhongcaoji.db")
CONTENT_ENGINE_TYPE = os.getenv("CONTENT_ENGINE_TYPE", "rule_based").strip() or "rule_based"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai_compatible").strip() or "openai_compatible"
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15") or "15")
LLM_MAX_RETRIES = max(0, int(os.getenv("LLM_MAX_RETRIES", "1") or "1"))
POSTER_ENGINE_TYPE = os.getenv("POSTER_ENGINE_TYPE", "pillow").strip() or "pillow"


def _sqlite_path_from_url(database_url: str) -> Path:
    if database_url.startswith("sqlite:///"):
        raw_path = database_url.removeprefix("sqlite:///")
        path = Path(raw_path)
        return path if path.is_absolute() else BASE_DIR / path
    return DATA_DIR / "zhongcaoji.db"


DATABASE_PATH = _sqlite_path_from_url(DATABASE_URL)
