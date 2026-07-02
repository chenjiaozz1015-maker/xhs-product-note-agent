import asyncio
import uuid
from urllib.parse import urlencode

from app.main import app
from app.routes import pages
from app.services import db
from app.services.auth_service import get_user_by_email, get_user_quota


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
    assert user["monthly_quota"] == 10
    assert user["used_quota"] == 0


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


def test_logged_in_generate_enters_existing_flow(monkeypatch):
    client = _client(monkeypatch, "logged_in_generate")
    _register(client)

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
        "generate_posters",
        lambda *args, **kwargs: ["/static/generated/fake.png"],
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

    called = {"generate_posters": False}

    def _should_not_generate(*args, **kwargs):
        called["generate_posters"] = True
        return ["/static/generated/fake.png"]

    monkeypatch.setattr(pages, "generate_posters", _should_not_generate)

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
    assert called["generate_posters"] is False
    assert updated_user is not None
    assert updated_user["used_quota"] == 10


def test_home_displays_quota_for_logged_in_user(monkeypatch):
    client = _client(monkeypatch, "home_quota")
    _register(client)

    response = client.get("/")

    assert response.status_code == 200
    assert "本月剩余：10 / 10" in response.text
    assert "本月还可生成 10 次" in response.text


def test_quota_fallback_for_old_user_with_null_values(monkeypatch):
    client = _client(monkeypatch, "quota_fallback")
    _register(client)
    user = get_user_by_email("user@example.com")
    assert user is not None

    with db.get_connection() as connection:
        connection.execute(
            "UPDATE users SET monthly_quota = NULL, used_quota = NULL WHERE id = ?",
            (user["id"],),
        )
        connection.commit()

    quota = get_user_quota(int(user["id"]))

    assert quota == {"monthly_quota": 10, "used_quota": 0, "remaining_quota": 10}


def test_pricing_page_is_public(monkeypatch):
    client = _client(monkeypatch, "pricing")

    response = client.get("/pricing")

    assert response.status_code == 200
    assert "免费试用" in response.text
    assert "个人月卡" in response.text
    assert "商家月卡" in response.text
