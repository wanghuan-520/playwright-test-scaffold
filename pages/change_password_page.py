# ═══════════════════════════════════════════════════════════════
# Change Password Page Object
# ═══════════════════════════════════════════════════════════════
"""
Change Password（修改密码）页面对象。

证据来源（前端代码）：
- aevatar-agent-station-frontend:
  - src/app/admin/profile/change-password/page.tsx
  - src/components/profile/ChangePassword.tsx

后端契约（Swagger）：
- POST /api/account/my-profile/change-password
  - schema: Volo.Abp.Account.ChangePasswordInput
  - errors: Volo.Abp.Http.RemoteServiceErrorResponse
  - maxLength: 128（currentPassword/newPassword）
"""

from __future__ import annotations

import os
import re
from typing import Optional

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# 页面对象：ChangePasswordPage
# - 目标：封装稳定定位器 + 改密动作 + 网络可观测断言入口
# - 原则：短小直白，避免复杂分支
# ============================================================
class ChangePasswordPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # CONFIG
    # ═══════════════════════════════════════════════════════════════

    URL = os.getenv("CHANGE_PASSWORD_PATH", "/admin/profile/change-password")

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS（优先 name/role；必要时提供 aria 兜底）
    # ═══════════════════════════════════════════════════════════════

    CURRENT_PASSWORD_INPUT = "[name='currentPassword']"
    NEW_PASSWORD_INPUT = "[name='newPassword']"
    CONFIRM_PASSWORD_INPUT = "[name='confirmNewPassword']"

    SAVE_BUTTON = 'role=button[name="Save"]'

    # Toast/notification 兜底（不同 UI 框架都尽量兼容）
    TOAST_ANY = (
        ".Toastify__toast,"
        ".toast,"
        "[role='alert'],"
        "[role='status'],"
        ".ant-message-notice,"
        ".ant-notification-notice,"
        ".abp-notification"
    )

    # 页面加载指示器：输入框最稳定
    page_loaded_indicator = CURRENT_PASSWORD_INPUT

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    def navigate(self) -> None:
        logger.info(f"导航到 Change Password: {self.URL}")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        try:
            if self.is_visible(self.CURRENT_PASSWORD_INPUT, timeout=1500):
                return True
            # heading 兜底（中英文均支持）
            heading = self.page.locator("h1, h2, h3").filter(
                has_text=re.compile(r"(change\s+password|修改密码)", re.I)
            )
            if heading.first.is_visible(timeout=1500):
                return True
            if self.is_visible(self.SAVE_BUTTON, timeout=1500):
                return True
            return False
        except Exception:
            return False

    def is_login_page(self) -> bool:
        """粗判是否被重定向到了登录流程（未登录/租户选择等）。"""
        url = (self.page.url or "").lower()
        return ("/auth/login" in url) or ("/account/login" in url) or ("/auth/set-tenant" in url)

    # ═══════════════════════════════════════════════════════════════
    # FORM ACTIONS（敏感字段必须使用 secret_fill）
    # ═══════════════════════════════════════════════════════════════

    def fill_current_password(self, value: str) -> None:
        self.secret_fill(self.CURRENT_PASSWORD_INPUT, value)

    def fill_new_password(self, value: str) -> None:
        self.secret_fill(self.NEW_PASSWORD_INPUT, value)

    def fill_confirm_password(self, value: str) -> None:
        self.secret_fill(self.CONFIRM_PASSWORD_INPUT, value)

    def click_save(self) -> None:
        self.click(self.SAVE_BUTTON)

    # ═══════════════════════════════════════════════════════════════
    # NETWORK-AWARE SAVE
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _is_change_password_response(resp) -> bool:
        try:
            return (
                ("/api/account/my-profile/change-password" in (resp.url or ""))
                and (resp.request.method == "POST")
            )
        except Exception:
            return False

    def click_save_and_wait_change_password(self, timeout_ms: int = 15000):
        """
        点击 Save 并等待 change-password 响应返回。
        Returns: playwright.sync_api.Response
        """
        with self.page.expect_response(self._is_change_password_response, timeout=timeout_ms) as resp_info:
            self.click_save()
        resp = resp_info.value
        try:
            if resp is not None and resp.ok:
                setattr(self, "_change_password_ok_in_test", True)
        except Exception:
            pass
        return resp

    def click_save_and_capture_change_password(self, timeout_ms: int = 1500):
        """
        点击 Save，并尽力捕获 change-password 响应：
        - 若前端拦截（不发请求）：返回 None
        - 若确实发请求：返回 Response
        """
        try:
            with self.page.expect_response(self._is_change_password_response, timeout=timeout_ms) as resp_info:
                self.click_save()
            resp = resp_info.value
            try:
                if resp is not None and resp.ok:
                    setattr(self, "_change_password_ok_in_test", True)
            except Exception:
                pass
            return resp
        except Exception:
            return None

    # ═══════════════════════════════════════════════════════════════
    # UI EVIDENCE HELPERS
    # ═══════════════════════════════════════════════════════════════

    def wait_for_any_toast(self, timeout_ms: int = 3000) -> None:
        """等待任意 toast/notification 出现（不绑定具体文案）。"""
        self.page.wait_for_selector(self.TOAST_ANY, state="visible", timeout=timeout_ms)

    def wait_for_toasts_to_disappear(self, timeout_ms: int = 8000) -> None:
        """等待 toast 消失（用于避免截图污染）。"""
        try:
            self.page.wait_for_selector(self.TOAST_ANY, state="detached", timeout=timeout_ms)
        except Exception:
            # 某些 toast 会长期驻留，超时不阻塞主流程
            return

    def get_html5_validation_message(self, selector: str) -> str:
        """读取浏览器级校验文案（HTML5 validationMessage）。"""
        try:
            return self.page.eval_on_selector(selector, "el => el.validationMessage || ''")
        except Exception:
            return ""

    def report_validity(self, selector: str) -> None:
        """触发浏览器 reportValidity（尽力弹出原生校验气泡）。"""
        try:
            self.page.eval_on_selector(selector, "el => (el.reportValidity ? el.reportValidity() : false)")
        except Exception:
            return

    def get_abp_validation_errors(self, resp) -> list[dict]:
        """
        从 ABP 标准错误结构中提取 validationErrors（若存在）。
        """
        try:
            data = resp.json()
        except Exception:
            return []
        err = (data or {}).get("error") or {}
        if not isinstance(err, dict):
            return []
        ves = err.get("validationErrors") or err.get("validation_errors") or []
        if isinstance(ves, list):
            return [v for v in ves if isinstance(v, dict)]
        return []


