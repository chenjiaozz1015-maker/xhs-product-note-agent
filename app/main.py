from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import (
    APP_NAME,
    APP_VERSION,
    CONTENT_ENGINE_TYPE,
    GENERATED_DIR,
    POSTER_ENGINE_TYPE,
    SESSION_SECRET,
    STATIC_DIR,
    UPLOAD_DIR,
)
from app.middleware.session import SignedCookieSessionMiddleware
from app.routes.auth import router as auth_router
from app.routes.pages import router as pages_router
from app.services.config_center_client import get_config_center_settings, get_runtime_token_summary
from app.services.image_composer import get_cjk_font_path
from app.services.llm_content_service import get_llm_config_status
from app.services.settings_service import app_settings_status
from app.services.runtime_config_service import get_runtime_config_value

app = FastAPI(title=APP_NAME)
app.add_middleware(SignedCookieSessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(auth_router)
app.include_router(pages_router)


@app.get("/health")
async def health() -> dict:
    font_path = get_cjk_font_path()
    content_engine_setting = get_runtime_config_value("CONTENT_ENGINE_TYPE", default=CONTENT_ENGINE_TYPE)
    resolved_content_engine = str(content_engine_setting["value"] or "rule_based")
    llm_status = get_llm_config_status(resolved_content_engine)
    config_center_settings = get_config_center_settings()
    runtime_token_summary = get_runtime_token_summary()
    app_settings = app_settings_status()
    return {
        "status": "ok",
        "app": "zhongcaoji",
        "version": APP_VERSION,
        "content_engine_type": resolved_content_engine,
        "content_engine_type_source": content_engine_setting["source"],
        "poster_engine_type": POSTER_ENGINE_TYPE,
        "llm_provider": llm_status.llm_provider,
        "llm_provider_source": llm_status.llm_provider_source,
        "llm_config_ready": llm_status.llm_config_ready,
        "llm_base_url_configured": llm_status.llm_base_url_status == "configured",
        "llm_base_url_source": llm_status.llm_base_url_source,
        "llm_model_configured": llm_status.llm_model_status == "configured",
        "llm_model_source": llm_status.llm_model_source,
        "llm_api_key_configured": llm_status.llm_api_key_status == "configured",
        "llm_api_key_source": llm_status.llm_api_key_source,
        "llm_timeout_seconds_source": llm_status.llm_timeout_seconds_source,
        "llm_max_retries_source": llm_status.llm_max_retries_source,
        "uploads_dir_exists": UPLOAD_DIR.exists(),
        "generated_dir_exists": GENERATED_DIR.exists(),
        "static_dir_exists": STATIC_DIR.exists(),
        "css_file_exists": (STATIC_DIR / "css" / "style.css").exists(),
        "js_file_exists": (STATIC_DIR / "js" / "app.js").exists(),
        "font_file_exists": font_path is not None,
        "font_path": str(font_path) if font_path else None,
        "config_center_project_code": config_center_settings["project_code"],
        "config_center_env": config_center_settings["env"],
        "config_center_runtime_token_ready": runtime_token_summary["runtime_token_ready"],
        "app_settings_ready": bool(app_settings["ready"]),
        "app_settings_count": int(app_settings["count"]),
    }
