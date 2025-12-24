"""
# ═══════════════════════════════════════════════════════════════
# Login Page Object (ABP)
# ═══════════════════════════════════════════════════════════════
#
# 背景：
# - 本项目的前端登录入口通常是 /auth/login
# - 它会重定向到 ABP 的 /Account/Login，并使用以下表单控件：
#   - #LoginInput_UserNameOrEmailAddress
#   - #LoginInput_Password
#   - button[name='Action'][type='submit']
#
# 设计原则（ASCII 分块注释）：
# ------------------------------------------------------------
# - 只做一件事：把“登录”变成可复用的稳定动作
# - 不把密码写进日志
# - 不绑定具体业务页面：登录成功的判定交给调用方（例如打开目标页/调用后端接口验证）
# ------------------------------------------------------------
"""

from __future__ import annotations

import os
import time
from typing import Optional

from playwright.sync_api import Page

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """
    ABP 登录页对象（支持 /auth/login 重定向链路）。
    """

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    USERNAME_OR_EMAIL = "#LoginInput_UserNameOrEmailAddress"
    PASSWORD = "#LoginInput_Password"
    SUBMIT = "button[name='Action'][type='submit']"

    # 前端入口（会重定向到 /Account/Login）
    URL = "/auth/login"

    # 页面加载指示器：用户名输入框可见即可
    page_loaded_indicator = USERNAME_OR_EMAIL

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    def navigate(self) -> None:
        logger.info("导航到登录入口: /auth/login")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        try:
            return self.is_visible(self.USERNAME_OR_EMAIL, timeout=10_000)
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def login(self, *, username: str, password: str) -> None:
        """
        执行登录提交。

        注意：
        - 这里只负责“填写并提交”
        - 登录成功/失败的业务判定（例如是否跳转到目标页、是否出现 toast）由调用方处理
        """
        logger.info(f"执行登录: {username}")
        # 避免误用：如果调用方没先 navigate，就这里补一次
        if not self.is_loaded():
            self.navigate()

        # 用户名：允许走 BasePage.fill（日志包含 username，通常不属于敏感信息）
        self.fill(self.USERNAME_OR_EMAIL, username)

        # 密码：禁止 BasePage.fill/PageActions.fill（会把 value 打到 debug 日志）
        logger.info("填写密码: ***")
        self.page.wait_for_selector(self.PASSWORD, state="visible", timeout=30_000)
        self.page.fill(self.PASSWORD, password, timeout=30_000)

        # 提交：尽量等待一次导航（ABP 登录通常会有 form submit -> redirect）
        try:
            with self.page.expect_navigation(wait_until="domcontentloaded", timeout=30_000):
                self.page.click(self.SUBMIT)
        except Exception:
            # 有些环境会通过 JS/XHR，或导航发生得很快；这里不强制
            try:
                self.page.click(self.SUBMIT)
            except Exception:
                pass

        # ═══════════════════════════════════════════════════════════════
        # 等待“前端登录态真正建立”
        # ═══════════════════════════════════════════════════════════════
        #
        # 现象：
        # - OIDC 回跳到前端后，前端还需要一段时间写入 session
        # - 如果此时立刻导航到受保护路由（如 /admin/profile/change-password），会被中间态踢回 "/"
        #
        # 策略（双保险）：
        # - 等 URL 回到 frontend 域（base_url）
        # - 轮询 /api/abp/application-configuration，直到 currentUser.isAuthenticated=true
        # - 同时等待 UI 上出现用户菜单按钮（Toggle user menu）
        frontend = (self.base_url or "").rstrip("/")
        if frontend:
            # 允许回跳更久：OIDC/自签环境可能较慢
            deadline_ms = int(os.getenv("LOGIN_SESSION_TIMEOUT_MS", "60000"))

            def _has_login_error_text() -> Optional[str]:
                # ABP 常见文案（中英文）
                for t in [
                    "Invalid username or password",
                    "登录失败",
                    "用户名或密码无效",
                    "locked",
                    "已锁定",
                ]:
                    try:
                        if self.page.get_by_text(t, exact=False).is_visible(timeout=200):
                            return t
                    except Exception:
                        pass
                return None

            cfg_ok = False
            start = int(time.time() * 1000)
            last_url = None
            while (int(time.time() * 1000) - start) < deadline_ms:
                try:
                    last_url = self.page.url
                except Exception:
                    last_url = None

                # 0) 若仍停留在 /Account/Login，优先检查是否有明确失败文案
                err_txt = _has_login_error_text()
                if err_txt:
                    # 标记本地账号池不可用，避免被反复分配导致整套 suite 失败
                    try:
                        from utils.data_manager import DataManager

                        DataManager().mark_account_locked(username, reason=f"login_failed:{err_txt}")
                    except Exception:
                        pass
                    raise AssertionError(f"登录失败（检测到错误文案: {err_txt}），url={last_url}")

                # 1) 前端权威：application-configuration
                try:
                    r = self.page.context.request.get(f"{frontend}/api/abp/application-configuration")
                    if r.ok:
                        j = r.json() or {}
                        cu = (j.get("currentUser") or {})
                        if cu.get("isAuthenticated") is True:
                            cfg_ok = True
                            break
                except Exception:
                    pass

                # 2) URL 已回到前端域也算成功（后续页面再自行验证）
                try:
                    if last_url and last_url.startswith(frontend):
                        cfg_ok = True
                        break
                except Exception:
                    pass

                try:
                    self.page.wait_for_timeout(250)
                except Exception:
                    pass

            # 3) UI 证据：用户菜单按钮出现（更贴近真实用户）
            if cfg_ok:
                try:
                    self.page.wait_for_selector(
                        r'role=button[name=/(toggle\\s+user\\s+menu|用户菜单|账户菜单)/i]',
                        state="visible",
                        timeout=10_000,
                    )
                except Exception:
                    pass

            if not cfg_ok:
                try:
                    self.take_screenshot("login_session_not_ready", full_page=True)
                except Exception:
                    pass
                raise AssertionError(f"登录后未建立前端会话（isAuthenticated!=true），url={last_url}")


