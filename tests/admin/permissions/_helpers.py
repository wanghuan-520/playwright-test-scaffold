# ═══════════════════════════════════════════════════════════════
# Admin Permissions - Test Helpers
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import allure
from playwright.sync_api import Page
from pages.admin_permissions_page import AdminPermissionsPage
from utils.logger import get_logger

logger = get_logger(__name__)


def assert_not_redirected_to_login(page: Page) -> None:
    """断言未被重定向到登录页"""
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {url}"
    assert "/login" not in url.lower(), f"redirected to login: {url}"


def step_shot(page_obj, name: str, *, full_page: bool = True) -> None:
    """关键步骤截图"""
    try:
        screenshot = page_obj.page.screenshot(full_page=full_page)
        allure.attach(screenshot, name, allure.attachment_type.PNG)
    except Exception:
        pass


# Toast / Notification 选择器
TOAST_SELECTORS = (
    "[role='region'][aria-label*='Notification'] li, "
    ".sonner-toast, [data-sonner-toast], "
    "[role='alert'], .toast"
)


def get_toast_text(page: Page) -> str:
    try:
        toast = page.locator(TOAST_SELECTORS).first
        if toast.is_visible(timeout=1000):
            return (toast.inner_text(timeout=2000) or "").strip()
    except Exception:
        pass
    return ""


def navigate_and_wait(page_obj: AdminPermissionsPage, auth_page: Page) -> None:
    """导航到 Permissions 页面并等待数据完全加载"""
    page_obj.navigate()
    assert_not_redirected_to_login(auth_page)
    loaded = page_obj.wait_for_permissions_loaded(timeout=20000)
    if not loaded:
        # 重试一次
        auth_page.reload()
        auth_page.wait_for_timeout(3000)
        page_obj.wait_for_permissions_loaded(timeout=20000)
