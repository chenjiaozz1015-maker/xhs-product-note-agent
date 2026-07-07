from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil

from app.config import APP_TITLE, APP_VERSION, UPLOAD_DIR, GENERATED_DIR
from app.services.auth_service import (
    get_current_user,
    get_effective_plan_config,
    get_user_quota,
    increment_used_quota,
)
from app.services.note_builder import build_result_payload
from app.services.plan_service import get_default_trial_plan
from app.services.poster_engine_adapter import PosterRenderInput, PosterRenderResult, render_posters
from app.services.record_service import create_generation_record, list_recent_generation_records

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _index_context(request: Request, error: str = "", warning: str = "") -> dict:
    current_user = get_current_user(request)
    quota = get_user_quota(int(current_user["id"])) if current_user else None
    current_plan = get_effective_plan_config(current_user) if current_user else None
    recent_records = list_recent_generation_records(int(current_user["id"])) if current_user else []
    return {
        "request": request,
        "app_title": APP_TITLE,
        "app_version": APP_VERSION,
        "current_user": current_user,
        "current_plan": current_plan,
        "trial_plan": get_default_trial_plan(),
        "quota": quota,
        "recent_records": recent_records,
        "error": error,
        "warning": warning,
    }


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", _index_context(request))


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    product_name: str = Form(""),
    category: str = Form("其他好物"),
    description: str = Form(""),
    content_type: str = Form(...),
    style: str = Form(...),
    image: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login?next=/&login_required=1", status_code=303)

    quota = get_user_quota(int(current_user["id"]))
    if not quota or quota["remaining_quota"] <= 0:
        return templates.TemplateResponse(
            "quota_empty.html",
            {
                "request": request,
                "app_title": APP_TITLE,
                "app_version": APP_VERSION,
                "current_user": current_user,
                "current_plan": get_effective_plan_config(current_user),
                "trial_plan": get_default_trial_plan(),
                "quota": quota,
            },
            status_code=403,
        )

    if not image or not image.filename:
        return templates.TemplateResponse(
            "index.html",
            _index_context(request, error="请先上传一张商品图片"),
            status_code=400,
        )

    image_name = Path(image.filename).name
    image_suffix = Path(image_name).suffix.lower()
    if image_suffix not in SUPPORTED_IMAGE_EXTENSIONS or image.content_type not in SUPPORTED_IMAGE_TYPES:
        return templates.TemplateResponse(
            "index.html",
            _index_context(request, error="请上传 JPG、PNG 或 WEBP 格式的商品图片"),
            status_code=400,
        )

    try:
        save_path = UPLOAD_DIR / image_name
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = str(save_path)

        result_payload = build_result_payload(
            description,
            content_type,
            style,
            [],
            product_name=product_name,
            category=category,
        )
        poster_result = render_posters(
            PosterRenderInput(
                product_image_path=image_path,
                output_dir=str(GENERATED_DIR),
                product_name=product_name,
                category=category,
                content_type=content_type,
                style=style,
                note_data={
                    "cover_title": str(result_payload["cover_title"]),
                    "cover_subtitle": str(result_payload["cover_subtitle"]),
                    "selling_points": list(result_payload["selling_points"]),
                    "summary_title": str(result_payload["summary_title"]),
                    "suitable_for": str(result_payload["suitable_for"]),
                    "recommend_reason": str(result_payload["recommend_reason"]),
                    "summary_sentence": str(result_payload["summary_sentence"]),
                },
                image_count=3,
            )
        )
        result_payload["image_paths"] = poster_result.image_paths
        quota = increment_used_quota(int(current_user["id"]))
        create_generation_record(
            user_id=int(current_user["id"]),
            product_name=product_name,
            category=category,
            content_type=content_type,
            style=style,
            image_count=3,
            quota_cost=1,
            requested_engine_type=str(result_payload.get("content_engine_requested_type", "")),
            content_engine_type=str(result_payload.get("content_engine_type", "")),
            content_fallback_used=bool(result_payload.get("content_engine_fallback_used")),
            content_fallback_reason=str(result_payload.get("content_engine_fallback_reason", "")),
        )
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "app_title": APP_TITLE,
                "app_version": APP_VERSION,
                "current_user": get_current_user(request),
                "current_plan": get_effective_plan_config(current_user),
                "trial_plan": get_default_trial_plan(),
                "quota": quota,
                "result": result_payload,
            },
        )
    except Exception as error:
        print(f"Generate failed: {error}")
        return templates.TemplateResponse(
            "index.html",
            _index_context(request, error="生成失败，请重新上传图片再试一次"),
            status_code=500,
        )
