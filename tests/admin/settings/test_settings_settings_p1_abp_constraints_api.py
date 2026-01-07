import allure
import pytest
from playwright.sync_api import Page

from utils.config import ConfigManager


def _backend_base() -> str:
    """
    注意：本项目存在两个后端 host：
    - AuthServer (默认 44320)：承载 /Account/* 页面与部分 /api/account/*
    - BusinessServer HttpApi.Host (默认 44345)：承载 Setting/Feature/Identity 等管理 API

    通过 curl 探测可知：
    - https://localhost:44345/api/setting-management/emailing 支持 GET/POST（不支持 PUT）
    """
    backend = (ConfigManager().get_service_url("backend") or "").rstrip("/")
    # 默认把 44320 映射到 44345（仅用于管理类 API）
    if backend.endswith(":44320"):
        return backend[:-6] + ":44345"
    return backend


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AdminSettings")
@allure.story("P1 - ABP Constraints")
@allure.title("Emailing 更新：端口范围/必填字段（若无权限则应 403）")
def test_p1_emailing_update_constraints_or_forbidden(auth_page: Page):
    """
    需求文档约束：
    - smtpPort: 1..65535
    - defaultFromAddress/defaultFromDisplayName: required, minLength=1

    现实情况：
    - 在部分环境中，Feature `SettingManagement.AllowChangingEmailSettings` 可能为 false，
      或权限不足导致 403。此时用例以“后端必须明确拒绝（403）”视为通过。
    """
    page = auth_page
    base = _backend_base()

    bad_payload = {
        "smtpHost": "smtp.example.com",
        "smtpPort": 0,  # invalid
        "smtpUserName": "u",
        "smtpPassword": "p",
        "smtpDomain": "d",
        "smtpEnableSsl": True,
        "smtpUseDefaultCredentials": False,
        "defaultFromAddress": "",  # invalid (required, minLength=1)
        "defaultFromDisplayName": "",  # invalid (required, minLength=1)
    }

    # 运行时该接口允许的方法为 GET/POST（Allow: GET, POST）
    resp = page.request.post(f"{base}/api/setting-management/emailing", data=bad_payload)
    assert resp.status in {400, 401, 403}, f"expected 400/401/403 but got {resp.status}"
    if resp.status == 400:
        # 400 说明后端按 DTO/ABP rules 拒绝非法输入（符合要求）
        return
    if resp.status == 403:
        # 403 说明被 Feature/Policy 禁止更新（符合要求：后端必须拦截）
        return
    # 401: token/session invalid（环境问题），保守跳过避免误判
    pytest.skip("unauthorized session for emailing update (401)")


