# ═══════════════════════════════════════════════════════════════
# Personal Settings Page Object
# ═══════════════════════════════════════════════════════════════
"""
Personal Settings（个人设置）页面对象。

说明：
- 该页面在不同项目/版本下路由可能不同，因此默认 URL 可通过环境变量覆盖：
  - PERSONAL_SETTINGS_PATH：默认 "/admin/profile"
"""

import os
import re
from typing import Dict
import time

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class PersonalSettingsPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # CONFIG
    # ═══════════════════════════════════════════════════════════════

    URL = os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile")

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════

    USERNAME_INPUT = "#userName"
    NAME_INPUT = "#name"
    SURNAME_INPUT = "#surname"
    EMAIL_INPUT = "#email"
    PHONE_INPUT = "#phoneNumber"

    SAVE_BUTTON = "button[type='submit']"
    SUCCESS_TOAST_TEXT = "Profile has been updated successfully."

    # 页面加载指示器：这里用 body 做哨兵，避免因为 UI 变更导致等待卡死；
    # 真实“已加载”判断放在 is_loaded() 里做多策略探测。
    page_loaded_indicator = "body"

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    def navigate(self) -> None:
        """导航到 Personal Settings 页面"""
        logger.info(f"导航到 Personal Settings: {self.URL}")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        """
        检查页面是否加载完成（多策略，尽量不依赖脆弱 selector）。
        """
        try:
            # 0) 关键控件（最稳定）
            if self.is_visible(self.USERNAME_INPUT, timeout=1500) and self.is_visible(self.EMAIL_INPUT, timeout=1500):
                return True

            # 1) Heading 文案探测（中英文均支持）
            heading = self.page.locator("h1, h2").filter(
                has_text=re.compile(r"(personal\s+settings|profile|个人(设置|信息)|个人资料)", re.I)
            )
            if heading.first.is_visible(timeout=1500):
                return True

            # 2) 表单/保存按钮探测
            save_btn = self.page.locator("button").filter(
                has_text=re.compile(r"(save|保存|update|更新)", re.I)
            )
            if save_btn.first.is_visible(timeout=1500):
                return True

            # 3) 至少存在一个可交互输入控件（input/textarea/select 或 role=textbox）
            inputs = self.page.locator("input, textarea, select, [role='textbox']")
            if inputs.first.is_visible(timeout=1500):
                return True

            return False
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def is_login_page(self) -> bool:
        """粗判是否被重定向到了登录页"""
        url = (self.page.url or "").lower()
        return ("/auth/login" in url) or ("/account/login" in url)

    # ═══════════════════════════════════════════════════════════════
    # FORM
    # ═══════════════════════════════════════════════════════════════

    def read_form_values(self) -> Dict[str, str]:
        """读取表单当前值（用于回滚，避免污染账号资料）"""
        return {
            "userName": self.page.input_value(self.USERNAME_INPUT),
            "name": self.page.input_value(self.NAME_INPUT),
            "surname": self.page.input_value(self.SURNAME_INPUT),
            "email": self.page.input_value(self.EMAIL_INPUT),
            "phoneNumber": self.page.input_value(self.PHONE_INPUT),
        }

    def fill_form(self, values: Dict[str, str]) -> None:
        """填写表单（只更新传入字段）"""
        if "userName" in values:
            self.page.fill(self.USERNAME_INPUT, values["userName"])
        if "name" in values:
            self.page.fill(self.NAME_INPUT, values["name"])
        if "surname" in values:
            self.page.fill(self.SURNAME_INPUT, values["surname"])
        if "email" in values:
            self.page.fill(self.EMAIL_INPUT, values["email"])
        if "phoneNumber" in values:
            self.page.fill(self.PHONE_INPUT, values["phoneNumber"])
        # 给 React/表单状态一个极小的刷新窗口：
        # - 之前“每步截图”隐含了等待，FAST 模式跳过截图后容易出现 fill→click 太快导致 submit 不触发
        # - 50ms 对总耗时几乎无影响，但显著提升稳定性
        self.page.wait_for_timeout(50)

    def click_save(self) -> None:
        """点击保存"""
        self.page.click(self.SAVE_BUTTON)

    # ═══════════════════════════════════════════════════════════════
    # NETWORK-AWARE SAVE (avoid toast-only assertions)
    # ═══════════════════════════════════════════════════════════════

    def save_and_wait_profile_update(self, timeout_ms: int = 15000):
        """
        点击 Save 并等待后端 profileUpdate 请求返回。

        设计意图：
        - toast 属于 UI 层“副作用”，可能被动画/定时/渲染策略影响而不稳定
        - 以网络响应作为主断言更可靠（且便于诊断：status/response）

        Returns:
            playwright.sync_api.Response
        """
        def _match(resp):
            try:
                return (
                    ("/api/account/my-profile" in (resp.url or ""))
                    and (resp.request.method == "PUT")
                )
            except Exception:
                return False

        with self.page.expect_response(_match, timeout=timeout_ms) as resp_info:
            self.click_save()

        resp = resp_info.value
        # 记录：本次用例期间是否真正“写成功”过（用于 teardown 是否需要回滚）
        try:
            if resp is not None and resp.ok:
                setattr(self, "_profile_update_ok_in_test", True)
        except Exception:
            pass
        return resp

    def click_save_and_capture_profile_update(self, timeout_ms: int = 1500):
        """
        点击 Save，并“尽力捕获” profileUpdate 响应：

        - 若前端校验拦截导致不发请求：返回 None
        - 若确实发出请求：返回 Response

        设计点：
        - 使用 expect_response 包裹 click，可避免“请求太快导致 wait_for_response 监听不到”的竞态。
        """
        def _match(resp):
            try:
                return (
                    ("/api/account/my-profile" in (resp.url or ""))
                    and (resp.request.method == "PUT")
                )
            except Exception:
                return False

        try:
            with self.page.expect_response(_match, timeout=timeout_ms) as resp_info:
                self.click_save()
            resp = resp_info.value
            try:
                if resp is not None and resp.ok:
                    setattr(self, "_profile_update_ok_in_test", True)
            except Exception:
                pass
            return resp
        except Exception:
            return None

    def wait_for_profile_update_response(self, timeout_ms: int = 1500):
        """
        仅等待 profileUpdate 响应（不触发点击）。

        用途：
        - 判断某次点击是否被浏览器/前端校验拦截（例如 HTML5 email validity）
        """
        def _match(resp):
            try:
                return ("/api/account/my-profile" in (resp.url or "")) and (resp.request.method == "PUT")
            except Exception:
                return False

        try:
            return self.page.wait_for_response(_match, timeout=timeout_ms)
        except Exception:
            return None

    def wait_for_save_success(self, timeout_ms: int = 8000) -> None:
        """
        等待保存成功提示。
        
        说明：
        - UI 可能存在文案/i18n 差异，因此采用“先精确、再兜底”的策略。
        """
        try:
            self.page.wait_for_selector(f"text={self.SUCCESS_TOAST_TEXT}", state="visible", timeout=timeout_ms)
            return
        except Exception:
            pass

        # 兜底：等 role=status 出现并包含 Success/updated 语义
        status = self.page.get_by_role("status")
        status.wait_for(state="visible", timeout=timeout_ms)
        text = (status.text_content() or "").lower()
        if ("success" not in text) and ("updated" not in text) and ("成功" not in text) and ("更新" not in text):
            raise AssertionError(f"未检测到明确的保存成功提示，status_text={text[:200]}")

    # ═══════════════════════════════════════════════════════════════
    # TOAST / NOTIFICATION STABILIZATION
    # ═══════════════════════════════════════════════════════════════

    def _toast_locator(self):
        """
        兜底 toast/notification 容器选择器集合。

        目标：
        - 不绑定某一个 UI 框架（Toastify/AntD/ABP/自研）
        - 为“截图稳定性”服务：等待 toast 出现/消失，避免截到上一条用例/上一步残留
        """
        return self.page.locator(
            ",".join(
                [
                    ".Toastify__toast",
                    ".toast",
                    "[role='alert']",
                    "[role='status']",
                    ".ant-message-notice",
                    ".ant-notification-notice",
                    ".abp-notification",
                ]
            )
        )

    def wait_for_toasts_to_disappear(self, timeout_ms: int = 8000) -> None:
        """
        等待页面上的 toast/notification 消失（用于避免“成功 toast + 错误 toast 同框截图”的干扰）。

        注意：
        - 这是“截图稳定性”的工程化妥协：宁可多等一会儿，也不要把上一条 toast 带进下一步截图。
        - 不保证 100%（某些 toast 可能长期驻留），超时则直接返回，不阻塞测试主流程。
        """
        end = time.time() + (timeout_ms / 1000.0)
        loc = self._toast_locator()

        while time.time() < end:
            try:
                cnt = loc.count()
            except Exception:
                cnt = 0

            if cnt <= 0:
                return

            any_visible = False
            # 最多探测前 6 个，避免过多 RPC
            for i in range(min(cnt, 6)):
                try:
                    if loc.nth(i).is_visible(timeout=200):
                        any_visible = True
                        break
                except Exception:
                    continue

            if not any_visible:
                return

            try:
                self.page.wait_for_timeout(200)
            except Exception:
                return

    def wait_for_text_visible(self, text: str, timeout_ms: int = 5000) -> None:
        """等待任意包含指定文本的提示出现（toast/inline 都可）。"""
        self.page.get_by_text(text, exact=False).first.wait_for(state="visible", timeout=timeout_ms)

    def show_html5_validation_bubble(self, selector: str, timeout_ms: int = 1500) -> None:
        """
        尝试让浏览器弹出 HTML5 validation 气泡（reportValidity）。

        说明：
        - 某些平台/浏览器的“原生气泡”可能不进入截图（系统级 UI），但 reportValidity 至少能稳定触发 validity 状态
        - 我们同时会高亮输入框 + 截取输入框局部，保证报告“可读”
        """
        try:
            loc = self.page.locator(selector).first
            loc.scroll_into_view_if_needed(timeout=timeout_ms)
            loc.click(timeout=timeout_ms)
        except Exception:
            pass

        try:
            # reportValidity 会触发原生气泡（若浏览器支持），并返回 bool
            self.page.eval_on_selector(selector, "el => (el.reportValidity ? el.reportValidity() : false)")
        except Exception:
            pass

        try:
            self.page.wait_for_timeout(200)
        except Exception:
            pass

    def disable_form_validation(self, selector_in_form: str = None) -> None:
        """
        禁用浏览器原生表单校验（HTML5 constraint validation）。

        目的：
        - 以 ABP 后端校验为准时，需要确保请求能发到后端，而不是被浏览器气泡拦截。
        """
        selector = selector_in_form or self.SAVE_BUTTON
        try:
            self.page.eval_on_selector(
                selector,
                """el => {
                  const form = el.closest && el.closest('form');
                  if (form) form.noValidate = true;
                }""",
            )
        except Exception:
            # 不让该诊断/兼容逻辑影响测试主流程
            pass

    def set_value_js(self, selector: str, value: str) -> None:
        """
        用 JS 直接写入 input 的 value，并派发 input/change 事件。

        目的：
        - 绕过某些输入类型（如 type=email）在 UI 层的拦截，让请求进入后端校验链路。
        """
        try:
            self.page.eval_on_selector(
                selector,
                """(el, v) => {
                  el.focus();
                  el.value = v;
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                  el.blur();
                }""",
                value,
            )
        except Exception:
            # fallback：用 fill（可能触发浏览器拦截，但至少不崩）
            try:
                self.page.fill(selector, value)
            except Exception:
                pass

    def get_abp_validation_errors(self, resp) -> list[dict]:
        """
        从 ABP 标准错误结构中提取 validationErrors（若存在）。

        常见结构（ABP）：
        {
          "error": {
            "code": "...",
            "message": "...",
            "details": "...",
            "validationErrors": [{ "message": "...", "members": ["Email"] }]
          }
        }
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

    def take_element_screenshot(self, selector: str, name: str = "element_screenshot") -> str:
        """
        截取元素局部截图（用于让字段级错误/气泡更清晰）。
        同时仍建议保留 full_page 截图（Allure 规范）。
        """
        from pathlib import Path
        from datetime import datetime
        import allure

        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = screenshot_dir / filename

        # 尽量把元素滚到视口中间
        try:
            self.page.eval_on_selector(selector, "el => el.scrollIntoView({block: 'center', inline: 'center'})")
        except Exception:
            pass

        # 高亮边框，增强可读性（截图后自动恢复）
        try:
            self.page.eval_on_selector(
                selector,
                "el => { el.__qa_prev_outline = el.style.outline; el.style.outline = '3px solid #ff4d4f'; }",
            )
        except Exception:
            pass

        try:
            shot = self.page.locator(selector).first.screenshot()
        finally:
            try:
                self.page.eval_on_selector(
                    selector,
                    "el => { if (el.__qa_prev_outline !== undefined) { el.style.outline = el.__qa_prev_outline; delete el.__qa_prev_outline; } }",
                )
            except Exception:
                pass

        with open(filepath, "wb") as f:
            f.write(shot)

        allure.attach(shot, name=name, attachment_type=allure.attachment_type.PNG)
        logger.info(f"元素截图已保存: {filepath}")
        return str(filepath)

    def get_email_validation_message(self) -> str:
        """读取 email 输入框的浏览器级校验文案（HTML5 validationMessage）。"""
        try:
            return self.page.eval_on_selector(self.EMAIL_INPUT, "el => el.validationMessage || ''")
        except Exception:
            return ""


