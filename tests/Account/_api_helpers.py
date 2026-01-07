"""
Account API helpers (ABP AuthServer).

目的：
- 用 API 级别的 4xx 断言覆盖 ABP 的 Required/MaxLength/Format 等权威约束
- 避免 UI 提交造成副作用（例如真实注册/发邮件）
"""

from __future__ import annotations

from typing import Any, Dict

from playwright.sync_api import Page

from utils.config import ConfigManager


def backend_base_url() -> str:
    cfg = ConfigManager()
    return (cfg.get_service_url("backend") or "").rstrip("/")


def app_name() -> str:
    # 来源：abp_app_config.json 的 localization 里显示 AppName=BusinessServer
    # swagger 的 RegisterDto/SendPasswordResetCodeDto 都要求 appName
    return "BusinessServer"


def post_json(page: Page, path: str, payload: Dict[str, Any], *, timeout_ms: int = 15000):
    url = f"{backend_base_url()}{path}"
    return page.request.post(url, data=payload, timeout=timeout_ms)


