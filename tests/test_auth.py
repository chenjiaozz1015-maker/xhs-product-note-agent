import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.main import app
from app.routes import pages
from app.services import db
from app.services.auth_service import get_user_by_email, get_user_quota
from app.services.plan_service import (
    get_default_trial_plan,
    get_plan_config,
    get_plan_period_days,
    get_plan_quota,
    list_public_plans,
)
from app.services.record_service import create_generation_record, list_recent_generation_records, list_user_generation_records


class Response:
    def __init__(self, status_code: int, headers: list[tuple[bytes, bytes]], body: bytes) -> None:
        self.status_code = status_code
        self.body = body
        self.text = body.decode("utf-8")
        self.headers = {}
        for key, value in headers:
            self.headers[key.decode("latin-1").lower()] = value.decode("latin-1")


class LocalClient:
    def __init__(self, asgi_app) -> None:
        self.app = asgi_app
        self.cookie = ""

    def get(self, path: str) -> Response:
        return asyncio.run(self._request("GET", path))

    def post(
        self,
        path: str,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        follow_redirects: bool = True,
    ) -> Response:
        return asyncio.run(self._request("POST", path, data=data or {}, files=files))

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> Response:
        body, content_type = self._encode_body(data or {}, files)
        headers = []
        if content_type:
            headers.append((b"content-type", content_type.encode("ascii")))
        if self.cookie:
            headers.append((b"cookie", self.cookie.encode("latin-1")))

        response_status = 0
        response_headers: list[tuple[bytes, bytes]] = []
        response_body = b""
        sent = False
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path.split("?", 1)[0],
            "raw_path": path.encode("ascii"),
            "query_string": path.split("?", 1)[1].encode("ascii") if "?" in path else b"",
            "headers": headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            nonlocal response_status, response_headers, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")

        await self.app(scope, receive, send)
        response = Response(response_status, response_headers, response_body)
        set_cookie = response.headers.get("set-cookie", "")
        if set_cookie:
            self.cookie = set_cookie.split(";", 1)[0]
        return response

    def _encode_body(
        self,
        data: dict[str, str],
        files: dict[str, tuple[str, bytes, str]] | None,
    ) -> tuple[bytes, str]:
        if not files:
            return urlencode(data).encode("utf-8"), "application/x-www-form-urlencoded"

        boundary = "----zhongcaojitest"
        chunks = []
        for name, value in data.items():
            chunks.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n".encode("utf-8")
            )
        for name, (filename, content, content_type) in files.items():
            chunks.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                    f"Content-Type: {content_type}\r\n\r\n"
                ).encode("utf-8")
                + content
                + b"\r\n"
            )
        chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _client(monkeypatch, name: str) -> LocalClient:
    database_path = f"file:test_auth_{name}_{uuid.uuid4().hex}?mode=memory&cache=shared"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db(database_path)
    return LocalClient(app)


def _register(client: LocalClient, email: str = "user@example.com", password: str = "secret123"):
    return client.post(
        "/register",
        data={
            "email": email,
            "display_name": "测试用户",
            "password": password,
            "confirm_password": password,
            "next": "/",
        },
        follow_redirects=False,
    )


def _record_count(user_id: int) -> int:
    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM generation_records WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return int(row["count"])


def _all_record_count() -> int:
    with db.get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM generation_records").fetchone()
        return int(row["count"])


def _quota_time(days_from_now: int) -> str:
    value = datetime.now(timezone.utc) + timedelta(days=days_from_now)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _set_user_quota(user_id: int, used_quota: int, quota_reset_at: str | None) -> None:
    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET used_quota = ?, quota_reset_at = ? WHERE id = ?",
            (used_quota, quota_reset_at, user_id),
        )
        connection.commit()


def _set_user_plan(user_id: int, plan_code: str) -> None:
    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET plan = ? WHERE id = ?",
            (plan_code, user_id),
        )
        connection.commit()


def test_plan_service_public_plans_and_quota_rules():
    plans = list_public_plans()
    codes = [plan["code"] for plan in plans]

    assert codes == ["trial", "personal", "business", "credits_100", "custom"]
    assert get_plan_quota("trial") == 10
    assert get_plan_period_days("trial") == 30
    assert get_plan_quota("personal") == 100
    assert get_plan_period_days("personal") == 30
    assert get_plan_quota("business") == 500
    assert get_plan_period_days("business") == 30
    assert get_default_trial_plan()["display_name"] == "免费试用"
    assert get_plan_config("trial")["short_name"] == "试用账号"


def test_register_success_creates_trial_user(monkeypatch):
    client = _client(monkeypatch, "register_success")

    response = _register(client)
    user = get_user_by_email("user@example.com")

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert user is not None
    assert user["email"] == "user@example.com"
    assert user["password_hash"] != "secret123"
    assert user["password_hash"].startswith("pbkdf2_sha256$")
    assert user["plan"] == "trial"
    assert user["trial_status"] == "trial"
    assert user["monthly_quota"] == get_default_trial_plan()["quota"]
    assert user["used_quota"] == 0
    assert user["quota_reset_at"]
    quota_reset_at = datetime.fromisoformat(str(user["quota_reset_at"]).replace("Z", "+00:00"))
    assert quota_reset_at > datetime.now(timezone.utc)
    assert quota_reset_at <= datetime.now(timezone.utc) + timedelta(days=get_default_trial_plan()["period_days"], minutes=1)


def test_duplicate_email_register_fails(monkeypatch):
    client = _client(monkeypatch, "duplicate")
    _register(client)

    response = _register(client)

    assert response.status_code == 400
    assert "已经注册" in response.text


def test_password_confirmation_mismatch_register_fails(monkeypatch):
    client = _client(monkeypatch, "mismatch")

    response = client.post(
        "/register",
        data={
            "email": "user@example.com",
            "password": "secret123",
            "confirm_password": "different",
        },
    )

    assert response.status_code == 400
    assert "不一致" in response.text


def test_login_success(monkeypatch):
    client = _client(monkeypatch, "login_success")
    _register(client)

    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "secret123", "next": "/"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_login_wrong_password_fails(monkeypatch):
    client = _client(monkeypatch, "login_wrong")
    _register(client)

    response = client.post(
        "/login",
        data={"email": "user@example.com", "password": "wrong-password", "next": "/"},
    )

    assert response.status_code == 400
    assert "邮箱或密码不正确" in response.text


def test_generate_requires_login(monkeypatch):
    client = _client(monkeypatch, "generate_requires_login")

    response = client.post(
        "/generate",
        data={"content_type": "好物推荐", "style": "清新简约"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")
    assert _all_record_count() == 0


def test_logged_in_generate_enters_existing_flow(monkeypatch):
    client = _client(monkeypatch, "logged_in_generate")
    _register(client)
    registered_user = get_user_by_email("user@example.com")
    assert registered_user is not None
    original_quota_reset_at = str(registered_user["quota_reset_at"])

    upload_dir = pages.UPLOAD_DIR
    generated_dir = pages.GENERATED_DIR
    monkeypatch.setattr(pages, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(pages, "GENERATED_DIR", generated_dir)
    monkeypatch.setattr(
        pages,
        "build_result_payload",
        lambda *args, **kwargs: {
            "cover_title": "测试标题",
            "cover_subtitle": "测试副标题",
            "selling_points": ["卖点一", "卖点二", "卖点三"],
            "summary_title": "总结标题",
            "suitable_for": "适合人群",
            "recommend_reason": "推荐理由",
            "summary_sentence": "总结句",
            "note_titles": ["标题一"],
            "note_body": "正文",
            "hashtags": ["#测试"],
            "comments": ["评论"],
            "product_name": "测试商品",
            "category": "其他好物",
        },
    )
    monkeypatch.setattr(
        pages,
        "render_posters",
        lambda *args, **kwargs: pages.PosterRenderResult(
            success=True,
            image_paths=["/static/generated/fake.png"],
            engine_type="pillow",
        ),
    )

    response = client.post(
        "/generate",
        data={
            "product_name": "测试商品",
            "category": "其他好物",
            "description": "描述",
            "content_type": "好物推荐",
            "style": "清新简约",
        },
        files={"image": ("sample.png", b"fake", "image/png")},
    )

    assert response.status_code == 200
    assert "标题一" in response.text
    assert "/static/generated/fake.png" in response.text
    user = get_user_by_email("user@example.com")
    assert user is not None
    assert user["used_quota"] == 1
    assert user["quota_reset_at"] == original_quota_reset_at
    records = list_user_generation_records(int(user["id"]))
    assert len(records) == 1
    assert records[0]["product_name"] == "测试商品"
    assert records[0]["category"] == "其他好物"
    assert records[0]["content_type"] == "好物推荐"
    assert records[0]["style"] == "清新简约"
    assert records[0]["image_count"] == 3
    assert records[0]["quota_cost"] == 1


def test_generate_with_exhausted_quota_is_blocked_and_not_incremented(monkeypatch):
    client = _client(monkeypatch, "exhausted_quota")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET used_quota = 10 WHERE id = ?",
            (user["id"],),
        )
        connection.commit()

    called = {"render_posters": False}

    def _should_not_generate(*args, **kwargs):
        called["render_posters"] = True
        return pages.PosterRenderResult(
            success=True,
            image_paths=["/static/generated/fake.png"],
            engine_type="pillow",
        )

    monkeypatch.setattr(pages, "render_posters", _should_not_generate)

    response = client.post(
        "/generate",
        data={
            "product_name": "娴嬭瘯鍟嗗搧",
            "category": "鍏朵粬濂界墿",
            "description": "鎻忚堪",
            "content_type": "濂界墿鎺ㄨ崘",
            "style": "娓呮柊绠€绾?",
        },
        files={"image": ("sample.png", b"fake", "image/png")},
    )
    updated_user = get_user_by_email("user@example.com")

    assert response.status_code == 403
    assert "本月试用额度已用完" in response.text
    assert called["render_posters"] is False
    assert updated_user is not None
    assert updated_user["used_quota"] == 10
    assert _record_count(int(user["id"])) == 0


def test_quota_not_reset_before_reset_time(monkeypatch):
    client = _client(monkeypatch, "quota_not_reset")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    reset_at = _quota_time(10)
    _set_user_quota(int(user["id"]), used_quota=4, quota_reset_at=reset_at)

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["used_quota"] == 4
    assert quota["remaining_quota"] == 6
    assert quota["quota_reset_at"] == reset_at


def test_quota_resets_after_reset_time(monkeypatch):
    client = _client(monkeypatch, "quota_resets")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_quota(int(user["id"]), used_quota=10, quota_reset_at=_quota_time(-1))

    quota = get_user_quota(int(user["id"]))
    updated_user = get_user_by_email("user@example.com")

    assert quota is not None
    assert quota["used_quota"] == 0
    assert quota["remaining_quota"] == 10
    assert datetime.fromisoformat(quota["quota_reset_at"].replace("Z", "+00:00")) > datetime.now(timezone.utc)
    assert updated_user is not None
    assert updated_user["used_quota"] == 0


def test_plan_change_to_personal_updates_quota_and_preserves_usage(monkeypatch):
    client = _client(monkeypatch, "plan_personal")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_quota(int(user["id"]), used_quota=3, quota_reset_at=_quota_time(10))
    _set_user_plan(int(user["id"]), "personal")

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["plan_code"] == "personal"
    assert quota["monthly_quota"] == 100
    assert quota["used_quota"] == 3
    assert quota["remaining_quota"] == 97


def test_plan_change_to_business_updates_quota(monkeypatch):
    client = _client(monkeypatch, "plan_business")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "business")

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["plan_code"] == "business"
    assert quota["monthly_quota"] == 500


def test_unknown_plan_falls_back_to_trial(monkeypatch):
    client = _client(monkeypatch, "plan_unknown")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "mystery")

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["plan_code"] == "trial"
    assert quota["monthly_quota"] == 10


def test_display_only_plans_fall_back_to_trial_quota(monkeypatch):
    client = _client(monkeypatch, "plan_display_only")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    for plan_code in ("credits_100", "custom"):
        _set_user_plan(int(user["id"]), plan_code)
        quota = get_user_quota(int(user["id"]))
        assert quota is not None
        assert quota["plan_code"] == "trial"
        assert quota["monthly_quota"] == 10


def test_expired_quota_resets_using_current_business_plan(monkeypatch):
    client = _client(monkeypatch, "plan_reset_business")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "business")
    _set_user_quota(int(user["id"]), used_quota=500, quota_reset_at=_quota_time(-1))

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["plan_code"] == "business"
    assert quota["monthly_quota"] == 500
    assert quota["used_quota"] == 0
    assert quota["remaining_quota"] == 500


def test_expired_quota_allows_generate_again(monkeypatch):
    client = _client(monkeypatch, "expired_quota_generate")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_quota(int(user["id"]), used_quota=10, quota_reset_at=_quota_time(-1))

    monkeypatch.setattr(
        pages,
        "build_result_payload",
        lambda *args, **kwargs: {
            "cover_title": "title",
            "cover_subtitle": "subtitle",
            "selling_points": ["point"],
            "summary_title": "summary",
            "suitable_for": "people",
            "recommend_reason": "reason",
            "summary_sentence": "sentence",
            "note_titles": ["title"],
            "note_body": "body",
            "hashtags": ["#tag"],
            "comments": ["comment"],
            "product_name": "product",
            "category": "category",
        },
    )
    monkeypatch.setattr(
        pages,
        "render_posters",
        lambda *args, **kwargs: pages.PosterRenderResult(
            success=True,
            image_paths=["/static/generated/fake.png"],
            engine_type="pillow",
        ),
    )

    response = client.post(
        "/generate",
        data={
            "product_name": "product",
            "category": "category",
            "description": "description",
            "content_type": "type",
            "style": "style",
        },
        files={"image": ("sample.png", b"fake", "image/png")},
    )
    quota = get_user_quota(int(user["id"]))

    assert response.status_code == 200
    assert quota is not None
    assert quota["used_quota"] == 1
    assert quota["remaining_quota"] == 9
    assert _record_count(int(user["id"])) == 1


def test_generate_form_error_does_not_create_record(monkeypatch):
    client = _client(monkeypatch, "form_error_record")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    response = client.post(
        "/generate",
        data={"content_type": "濂界墿鎺ㄨ崘", "style": "娓呮柊绠€绾?"},
    )

    assert response.status_code == 400
    assert _record_count(int(user["id"])) == 0


def test_generate_failure_does_not_create_record_or_deduct_quota(monkeypatch):
    client = _client(monkeypatch, "generate_failure_record")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    monkeypatch.setattr(
        pages,
        "build_result_payload",
        lambda *args, **kwargs: {
            "cover_title": "title",
            "cover_subtitle": "subtitle",
            "selling_points": [],
            "summary_title": "summary",
            "suitable_for": "people",
            "recommend_reason": "reason",
            "summary_sentence": "sentence",
            "note_titles": ["title"],
            "note_body": "body",
            "hashtags": [],
            "comments": [],
            "product_name": "product",
            "category": "category",
        },
    )

    def _fail_generate(*args, **kwargs):
        raise RuntimeError("poster failed")

    monkeypatch.setattr(pages, "render_posters", _fail_generate)

    response = client.post(
        "/generate",
        data={
            "product_name": "product",
            "category": "category",
            "description": "description",
            "content_type": "type",
            "style": "style",
        },
        files={"image": ("sample.png", b"fake", "image/png")},
    )
    updated_user = get_user_by_email("user@example.com")

    assert response.status_code == 500
    assert updated_user is not None
    assert updated_user["used_quota"] == 0
    assert _record_count(int(user["id"])) == 0


def test_home_displays_quota_for_logged_in_user(monkeypatch):
    client = _client(monkeypatch, "home_quota")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    quota = get_user_quota(int(user["id"]))
    assert quota is not None

    response = client.get("/")

    assert response.status_code == 200
    assert "本月剩余：10 / 10" in response.text
    assert "本月还可生成 10 次" in response.text
    assert get_plan_config("trial")["short_name"] in response.text
    assert quota["quota_reset_date"] in response.text


def test_home_displays_personal_plan_quota(monkeypatch):
    client = _client(monkeypatch, "home_personal_plan")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "personal")

    response = client.get("/")

    assert response.status_code == 200
    assert get_plan_config("personal")["short_name"] in response.text
    assert "100" in response.text


def test_records_page_requires_login(monkeypatch):
    client = _client(monkeypatch, "records_requires_login")

    response = client.get("/me/records")

    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_records_page_for_logged_in_user_shows_empty_state(monkeypatch):
    client = _client(monkeypatch, "records_empty")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    quota = get_user_quota(int(user["id"]))
    assert quota is not None

    response = client.get("/me/records")

    assert response.status_code == 200
    assert "records-empty" in response.text
    assert "records-summary-card" in response.text
    assert quota["quota_reset_date"] in response.text


def test_records_page_displays_business_plan_and_quota(monkeypatch):
    client = _client(monkeypatch, "records_business_plan")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "business")

    response = client.get("/me/records")

    assert response.status_code == 200
    assert get_plan_config("business")["short_name"] in response.text
    assert "500" in response.text


def test_home_shows_recent_records_for_logged_in_user(monkeypatch):
    client = _client(monkeypatch, "home_recent_records")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    create_generation_record(
        user_id=int(user["id"]),
        product_name="sample product",
        category="sample category",
        content_type="sample content",
        style="sample style",
    )

    response = client.get("/")
    records = list_recent_generation_records(int(user["id"]))

    assert response.status_code == 200
    assert len(records) == 1
    assert "recent-records-card" in response.text
    assert "sample product" in response.text


def test_records_page_for_logged_in_user_lists_records(monkeypatch):
    client = _client(monkeypatch, "records_list")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    create_generation_record(
        user_id=int(user["id"]),
        product_name="listed product",
        category="listed category",
        content_type="listed content",
        style="listed style",
    )

    response = client.get("/me/records")

    assert response.status_code == 200
    assert "listed product" in response.text
    assert "listed category" in response.text


def test_quota_fallback_for_old_user_with_null_values(monkeypatch):
    client = _client(monkeypatch, "quota_fallback")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET monthly_quota = NULL, used_quota = NULL, quota_reset_at = NULL WHERE id = ?",
            (user["id"],),
        )
        connection.commit()

    quota = get_user_quota(int(user["id"]))

    assert quota is not None
    assert quota["monthly_quota"] == get_default_trial_plan()["quota"]
    assert quota["used_quota"] == 0
    assert quota["remaining_quota"] == get_default_trial_plan()["quota"]
    assert quota["quota_reset_at"]
    assert quota["quota_reset_date"]


def test_pricing_page_shows_logged_in_quota(monkeypatch):
    client = _client(monkeypatch, "pricing_logged_in")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    quota = get_user_quota(int(user["id"]))
    assert quota is not None

    response = client.get("/pricing")

    assert response.status_code == 200
    assert quota["quota_reset_date"] in response.text
    assert get_plan_config("trial")["short_name"] in response.text
    assert "当前试用账号" in response.text


def test_pricing_page_marks_current_personal_plan(monkeypatch):
    client = _client(monkeypatch, "pricing_personal_current")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None
    _set_user_plan(int(user["id"]), "personal")

    response = client.get("/pricing")

    assert response.status_code == 200
    assert get_plan_config("personal")["short_name"] in response.text
    assert "当前套餐" in response.text
    assert "已开通更高套餐" in response.text


def test_pricing_page_is_public(monkeypatch):
    client = _client(monkeypatch, "pricing")

    response = client.get("/pricing")

    assert response.status_code == 200
    assert response.text.count("pricing-card") == 5
    for plan in list_public_plans():
        assert plan["display_name"] in response.text
        assert plan["price_label"] in response.text
    assert "注册试用" in response.text
