from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_PLAN_CODE = "trial"

_PLANS: dict[str, dict[str, Any]] = {
    "trial": {
        "code": "trial",
        "display_name": "免费试用",
        "short_name": "试用账号",
        "price_label": "0 元",
        "quota": 10,
        "period_days": 30,
        "description": "适合初次试用",
        "features": [
            "每 30 天 10 次生成",
            "可体验图片素材和发布文案",
            "适合初次试用",
        ],
        "badge": "适合试用",
        "payment_enabled": False,
        "button_label": {
            "anonymous": "注册试用",
            "current": "当前试用账号",
            "disabled": "注册试用",
        },
        "href": "/register",
    },
    "personal": {
        "code": "personal",
        "display_name": "个人月卡",
        "short_name": "个人月卡",
        "price_label": "9.9 元 / 月",
        "quota": 100,
        "period_days": 30,
        "description": "适合好物分享用户",
        "features": [
            "每 30 天 100 次生成",
            "支持标题、正文、标签编辑",
            "适合好物分享用户",
        ],
        "badge": "推荐",
        "payment_enabled": False,
        "button_label": "暂未开放支付",
        "href": "#",
    },
    "business": {
        "code": "business",
        "display_name": "商家月卡",
        "short_name": "商家月卡",
        "price_label": "29.9 元 / 月",
        "quota": 500,
        "period_days": 30,
        "description": "适合小商家、团购、微商",
        "features": [
            "每 30 天 500 次生成",
            "适合小商家、团购、微商",
            "后续可扩展批量生成",
        ],
        "badge": "",
        "payment_enabled": False,
        "button_label": "暂未开放支付",
        "href": "#",
    },
    "credits_100": {
        "code": "credits_100",
        "display_name": "次数包",
        "short_name": "次数包",
        "price_label": "9.9 元 / 100 次",
        "quota": 100,
        "period_days": None,
        "description": "不想包月时可购买次数",
        "features": [
            "不想包月时可购买次数",
            "次数长期有效规则后续确定",
        ],
        "badge": "",
        "payment_enabled": False,
        "button_label": "暂未开放支付",
        "href": "#",
    },
    "custom": {
        "code": "custom",
        "display_name": "定制版 / 私有部署",
        "short_name": "定制版",
        "price_label": "联系开通",
        "quota": None,
        "period_days": None,
        "description": "适合企业或私有部署",
        "features": [
            "私有部署",
            "自定义模板",
            "批量商品生成",
            "企业内使用",
        ],
        "badge": "",
        "payment_enabled": False,
        "button_label": "联系开通",
        "href": "mailto:hello@example.com",
    },
}


def get_plan_config(plan_code: str | None) -> dict[str, Any]:
    return deepcopy(_PLANS.get(plan_code or DEFAULT_PLAN_CODE, _PLANS[DEFAULT_PLAN_CODE]))


def list_public_plans() -> list[dict[str, Any]]:
    return [deepcopy(plan) for plan in _PLANS.values()]


def get_default_trial_plan() -> dict[str, Any]:
    return get_plan_config(DEFAULT_PLAN_CODE)


def get_plan_quota(plan_code: str | None) -> int | None:
    quota = get_plan_config(plan_code).get("quota")
    return int(quota) if quota is not None else None


def get_plan_period_days(plan_code: str | None) -> int | None:
    period_days = get_plan_config(plan_code).get("period_days")
    return int(period_days) if period_days else None


def get_plan_display_name(plan_code: str | None) -> str:
    return str(get_plan_config(plan_code).get("display_name") or "")


def get_plan_short_name(plan_code: str | None) -> str:
    plan = get_plan_config(plan_code)
    return str(plan.get("short_name") or plan.get("display_name") or "")
