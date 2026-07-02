from __future__ import annotations

import base64
import hashlib
import hmac
import json
from http.cookies import SimpleCookie
from typing import Any, Awaitable, Callable

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SignedCookieSessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        cookie_name: str = "zhongcaoji_session",
        max_age: int = 14 * 24 * 60 * 60,
    ) -> None:
        self.app = app
        self.secret_key = secret_key.encode("utf-8")
        self.cookie_name = cookie_name
        self.max_age = max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        cookie_value = self._get_cookie(scope)
        scope["session"] = self._load_session(cookie_value)
        had_cookie = bool(cookie_value)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                session = scope.get("session", {})
                if session:
                    headers.append("Set-Cookie", self._build_cookie(session))
                elif had_cookie:
                    headers.append("Set-Cookie", self._delete_cookie())
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _get_cookie(self, scope: Scope) -> str:
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_cookie = headers.get(b"cookie")
        if not raw_cookie:
            return ""
        cookies = SimpleCookie()
        cookies.load(raw_cookie.decode("latin-1"))
        morsel = cookies.get(self.cookie_name)
        return morsel.value if morsel else ""

    def _load_session(self, cookie_value: str) -> dict[str, Any]:
        try:
            payload, signature = cookie_value.rsplit(".", 1)
            expected = self._sign(payload)
            if not hmac.compare_digest(signature, expected):
                return {}
            decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
            data = json.loads(decoded.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _build_cookie(self, session: dict[str, Any]) -> str:
        raw = json.dumps(session, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload = base64.urlsafe_b64encode(raw).decode("ascii")
        value = f"{payload}.{self._sign(payload)}"
        return (
            f"{self.cookie_name}={value}; Path=/; Max-Age={self.max_age}; "
            "HttpOnly; SameSite=Lax"
        )

    def _delete_cookie(self) -> str:
        return f"{self.cookie_name}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"

    def _sign(self, payload: str) -> str:
        return hmac.new(self.secret_key, payload.encode("ascii"), hashlib.sha256).hexdigest()
