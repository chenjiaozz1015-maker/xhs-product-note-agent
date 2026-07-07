from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import APP_TITLE, APP_VERSION
from app.services.auth_service import (
    authenticate_user,
    create_user,
    get_effective_plan_config,
    get_current_user,
    get_user_quota,
    login_user,
    logout_user,
)
from app.services.plan_service import get_default_trial_plan, list_public_plans
from app.services.record_service import (
    get_record_content_engine_label,
    list_user_generation_records,
    summarize_record_engines,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _auth_context(request: Request, **extra: object) -> dict[str, object]:
    current_user = get_current_user(request)
    quota = get_user_quota(int(current_user["id"])) if current_user else None
    current_plan = get_effective_plan_config(current_user) if current_user else None
    return {
        "request": request,
        "app_title": APP_TITLE,
        "app_version": APP_VERSION,
        "current_user": current_user,
        "current_plan": current_plan,
        "trial_plan": get_default_trial_plan(),
        "quota": quota,
        **extra,
    }


def _safe_next(next_url: str) -> str:
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return "/"


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", _auth_context(request))


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(""),
    display_name: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    next: str = Form("/"),
):
    if not email.strip():
        return templates.TemplateResponse(
            "register.html",
            _auth_context(request, error="请填写邮箱。"),
            status_code=400,
        )
    if not password:
        return templates.TemplateResponse(
            "register.html",
            _auth_context(request, error="请填写密码。", email=email, display_name=display_name),
            status_code=400,
        )
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            _auth_context(request, error="密码至少需要 6 位。", email=email, display_name=display_name),
            status_code=400,
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            _auth_context(request, error="两次输入的密码不一致。", email=email, display_name=display_name),
            status_code=400,
        )

    try:
        user = create_user(email=email, password=password, display_name=display_name)
    except ValueError:
        return templates.TemplateResponse(
            "register.html",
            _auth_context(request, error="这个邮箱已经注册过，请直接登录。", email=email, display_name=display_name),
            status_code=400,
        )

    login_user(request, int(user["id"]))
    return RedirectResponse(_safe_next(next), status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    warning = ""
    if request.query_params.get("login_required"):
        warning = "请先登录后生成种草笔记。"
    return templates.TemplateResponse("login.html", _auth_context(request, warning=warning, next=_safe_next(next)))


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    next: str = Form("/"),
):
    user = authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            _auth_context(request, error="邮箱或密码不正确。", email=email, next=_safe_next(next)),
            status_code=400,
        )
    login_user(request, int(user["id"]))
    return RedirectResponse(_safe_next(next), status_code=303)


@router.post("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/", status_code=303)


@router.get("/me/records", response_class=HTMLResponse)
async def my_records(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login?next=/me/records&login_required=1", status_code=303)

    records = list_user_generation_records(int(current_user["id"]), limit=30)
    record_summary = summarize_record_engines(records)
    enriched_records = []
    for record in records:
        enriched_record = dict(record)
        enriched_record["content_engine_label"] = get_record_content_engine_label(record)
        fallback_reason = str(record.get("content_fallback_reason") or "").strip()
        enriched_record["content_engine_reason"] = fallback_reason.replace("_", " ") if fallback_reason else ""
        enriched_records.append(enriched_record)
    return templates.TemplateResponse(
        "records.html",
        _auth_context(request, records=enriched_records, record_summary=record_summary),
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    plans = list_public_plans()
    return templates.TemplateResponse("pricing.html", _auth_context(request, plans=plans))
