from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil

from app.config import APP_TITLE, STATIC_DIR, UPLOAD_DIR, GENERATED_DIR
from app.services.note_builder import build_result_payload
from app.services.poster_engine_adapter import generate_posters

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_title": APP_TITLE})


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    description: str = Form(...),
    content_type: str = Form(...),
    style: str = Form(...),
    image: UploadFile | None = File(None),
):
    image_name = "sample.jpg"
    if image and image.filename:
        image_name = Path(image.filename).name
        save_path = UPLOAD_DIR / image_name
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = str(save_path)
    else:
        image_path = str(STATIC_DIR / "template_assets" / "sample.jpg")
        if not Path(image_path).exists():
            image_path = str(STATIC_DIR / "template_assets" / "placeholder.png")

    poster_paths = generate_posters(image_path, output_dir=str(GENERATED_DIR), title=description)
    result_payload = build_result_payload(description, content_type, style, poster_paths)
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "app_title": APP_TITLE, "result": result_payload},
    )
