from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil

from app.config import APP_TITLE, APP_VERSION, UPLOAD_DIR, GENERATED_DIR
from app.services.note_builder import build_result_payload
from app.services.poster_engine_adapter import generate_posters

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _index_context(request: Request, error: str = "", warning: str = "") -> dict:
    return {
        "request": request,
        "app_title": APP_TITLE,
        "app_version": APP_VERSION,
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
        poster_paths = generate_posters(
            image_path,
            output_dir=str(GENERATED_DIR),
            title=str(result_payload["cover_title"]),
            subtitle=str(result_payload["cover_subtitle"]),
            selling_points=list(result_payload["selling_points"]),
            summary_title=str(result_payload["summary_title"]),
            suitable_for=str(result_payload["suitable_for"]),
            recommend_reason=str(result_payload["recommend_reason"]),
            summary_sentence=str(result_payload["summary_sentence"]),
        )
        result_payload["image_paths"] = poster_paths
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "app_title": APP_TITLE,
                "app_version": APP_VERSION,
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
