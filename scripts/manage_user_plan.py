from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import db
from app.services.auth_service import (
    ensure_user_quota_state,
    get_effective_plan_config,
    get_user_by_email,
    get_user_quota,
)
from app.services.plan_service import get_plan_display_name

SUPPORTED_PLAN_CODES = ("trial", "personal", "business")
DEFAULT_DB_PATH = ROOT_DIR / "data" / "zhongcaoji.db"


def _print(message: str = "") -> None:
    sys.stdout.write(f"{message}\n")


def _error(message: str) -> int:
    sys.stderr.write(f"{message}\n")
    return 1


def _resolve_db_path(raw_path: str | None) -> Path:
    selected = Path(raw_path) if raw_path else DEFAULT_DB_PATH
    return selected if selected.is_absolute() else (ROOT_DIR / selected).resolve()


def _configure_database(database_path: Path) -> None:
    if not database_path.exists():
        raise FileNotFoundError(
            "未找到数据库文件，请确认已在项目根目录运行，或通过 --db 指定数据库路径。"
        )
    db.DATABASE_PATH = database_path
    db.init_db(database_path)


def _get_user_or_raise(email: str) -> dict[str, Any]:
    user = get_user_by_email(email)
    if not user:
        raise LookupError(f"未找到用户：{email}")
    synced_user = ensure_user_quota_state(int(user["id"]))
    if not synced_user:
        raise LookupError(f"未找到用户：{email}")
    return synced_user


def _format_value(value: Any) -> str:
    return "-" if value in (None, "") else str(value)


def _quota_snapshot(user: dict[str, Any]) -> dict[str, Any]:
    quota = get_user_quota(int(user["id"])) or {}
    plan = get_effective_plan_config(user)
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name") or "",
        "plan": user.get("plan") or "",
        "plan_name": plan["short_name"],
        "monthly_quota": quota.get("monthly_quota", user.get("monthly_quota", 0)),
        "used_quota": quota.get("used_quota", user.get("used_quota", 0)),
        "remaining_quota": quota.get("remaining_quota", 0),
        "quota_reset_at": quota.get("quota_reset_at", user.get("quota_reset_at")),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }


def _print_snapshot(title: str, snapshot: dict[str, Any]) -> None:
    _print(title)
    _print(f"ID: {snapshot['id']}")
    _print(f"Email: {snapshot['email']}")
    _print(f"显示名称: {_format_value(snapshot['display_name'])}")
    _print(f"Plan: {snapshot['plan']}")
    _print(f"套餐: {snapshot['plan_name']}")
    _print(
        f"额度: {snapshot['used_quota']} / {snapshot['monthly_quota']} 已用，剩余 {snapshot['remaining_quota']}"
    )
    _print(f"下次重置: {_format_value(snapshot['quota_reset_at'])}")
    _print(f"创建时间: {_format_value(snapshot['created_at'])}")
    _print(f"最近登录: {_format_value(snapshot['last_login_at'])}")


def command_show(args: argparse.Namespace) -> int:
    try:
        _configure_database(_resolve_db_path(args.db))
        user = _get_user_or_raise(args.email)
    except (FileNotFoundError, LookupError) as exc:
        return _error(str(exc))

    _print_snapshot("用户信息：", _quota_snapshot(user))
    return 0


def command_set_plan(args: argparse.Namespace) -> int:
    if args.plan not in SUPPORTED_PLAN_CODES:
        return _error("当前脚本只支持 trial / personal / business")

    try:
        _configure_database(_resolve_db_path(args.db))
        before_user = _get_user_or_raise(args.email)
        before = _quota_snapshot(before_user)
        with db.get_connection() as connection:
            connection.execute(
                "UPDATE users SET plan = ? WHERE id = ?",
                (args.plan, int(before_user["id"])),
            )
            connection.commit()
        after_user = _get_user_or_raise(args.email)
        after = _quota_snapshot(after_user)
    except (FileNotFoundError, LookupError) as exc:
        return _error(str(exc))

    _print_snapshot("修改前：", before)
    _print("")
    _print_snapshot("修改后：", after)
    return 0


def command_list(args: argparse.Namespace) -> int:
    try:
        _configure_database(_resolve_db_path(args.db))
    except FileNotFoundError as exc:
        return _error(str(exc))

    with db.get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, email, display_name, plan, monthly_quota, used_quota, quota_reset_at, created_at
            FROM users
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (max(args.limit, 1),),
        ).fetchall()

    if not rows:
        _print("暂无用户。")
        return 0

    _print("最近用户：")
    for row in rows:
        user = ensure_user_quota_state(int(row["id"])) or dict(row)
        quota = get_user_quota(int(row["id"])) or {}
        plan_name = get_plan_display_name(user.get("plan"))
        _print(
            " | ".join(
                [
                    f"ID {user['id']}",
                    f"Email {user['email']}",
                    f"名称 {_format_value(user.get('display_name'))}",
                    f"Plan {user.get('plan')}",
                    f"套餐 {plan_name}",
                    f"额度 {quota.get('used_quota', user.get('used_quota', 0))}/{quota.get('monthly_quota', user.get('monthly_quota', 0))}",
                    f"重置 {quota.get('quota_reset_at', user.get('quota_reset_at')) or '-'}",
                    f"创建 {user.get('created_at') or '-'}",
                ]
            )
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="中心化运营脚本：查询并手动调整用户套餐。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show", help="按邮箱查看用户套餐和额度")
    show_parser.add_argument("--email", required=True, help="用户邮箱")
    show_parser.add_argument("--db", default=None, help="SQLite 数据库路径，默认 data/zhongcaoji.db")
    show_parser.set_defaults(handler=command_show)

    set_plan_parser = subparsers.add_parser("set-plan", help="按邮箱手动修改用户套餐")
    set_plan_parser.add_argument("--email", required=True, help="用户邮箱")
    set_plan_parser.add_argument("--plan", required=True, help="支持 trial / personal / business")
    set_plan_parser.add_argument("--db", default=None, help="SQLite 数据库路径，默认 data/zhongcaoji.db")
    set_plan_parser.set_defaults(handler=command_set_plan)

    list_parser = subparsers.add_parser("list", help="列出最近注册用户")
    list_parser.add_argument("--limit", type=int, default=20, help="最多展示多少位用户")
    list_parser.add_argument("--db", default=None, help="SQLite 数据库路径，默认 data/zhongcaoji.db")
    list_parser.set_defaults(handler=command_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
