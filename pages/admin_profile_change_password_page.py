# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AdminProfileChangePassword 页面对象
URL: https://localhost:3000/admin/profile/change-password
Type: SETTINGS
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger
from typing import Optional, Any, Dict, List
import re

logger = get_logger(__name__)


class AdminProfileChangePasswordPage(BasePage):
    """
    AdminProfileChangePassword 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # personal_settings | placeholder: personal_settings
    PERSONAL_SETTINGS_BUTTON = 'role=tab[name="Personal Settings"]'

    # change_password | placeholder: change_password
    CHANGE_PASSWORD_BUTTON = 'role=tab[name="Change Password"]'

    # current_password | placeholder: current_password
    CURRENT_PASSWORD_INPUT = 'role=textbox[name="Current password"]'

    # new_password | placeholder: new_password
    NEW_PASSWORD_INPUT = 'role=textbox[name="New password"]'

    # confirm_new_password | placeholder: confirm_new_password
    CONFIRM_NEW_PASSWORD_INPUT = 'role=textbox[name="Confirm new password"]'

    # toggle_user_menu | placeholder: toggle_user_menu
    TOGGLE_USER_MENU_BUTTON = 'role=button[name="Toggle user menu"]'

    # show_password | placeholder: show_password
    SHOW_PASSWORD_BUTTON = 'role=button[name="Show password"]'

    # save | placeholder: save
    # 兼容中英文按钮文案（避免语言环境导致 locator 找不到）
    # NOTE:
    # - 这里用纯 CSS selector 的 “selector list” 形式（逗号）以保证 Playwright selector engine 兼容。
    # - 不混用 role=... 与 CSS 选择器，避免在 page.click/is_visible 时被错误解析。
    SAVE_BUTTON = 'button:has-text("Save"), button:has-text("保存")'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # home | placeholder: home
    HOME_LINK = 'role=link[name="Home"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    
    URL = 'https://localhost:3000/admin/profile/change-password'
    page_loaded_indicator = SAVE_BUTTON

    # 后端 API（用于等待/取证）
    CHANGE_PASSWORD_API = "/api/account/my-profile/change-password"

    # 兼容旧测试命名：CONFIRM_PASSWORD_INPUT
    # （旧用例里把 confirm_new_password 简写成 confirm_password）
    CONFIRM_PASSWORD_INPUT = CONFIRM_NEW_PASSWORD_INPUT
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """
        导航到页面（增强并发稳定性）
        
        并发健壮性优化：
        - 确保表单元素完全可见可交互
        - 等待网络空闲（避免动态加载干扰表单填充）
        - 在高并发场景下避免"表单未加载完就开始填充"导致的失败
        """
        logger.info(f"导航到 AdminProfileChangePassword 页面")
        self.goto(self.URL)
        self.wait_for_page_load()
        
        # ✅ 并发健壮性：确保关键表单元素完全可用
        try:
            self.page.wait_for_selector(self.CURRENT_PASSWORD_INPUT, state="visible", timeout=5000)
            self.page.wait_for_selector(self.NEW_PASSWORD_INPUT, state="visible", timeout=5000)
            self.page.wait_for_selector(self.CONFIRM_NEW_PASSWORD_INPUT, state="visible", timeout=5000)
            self.page.wait_for_selector(self.SAVE_BUTTON, state="visible", timeout=5000)
            # 等待网络空闲（避免动态脚本加载干扰）
            self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception as e:
            logger.warning(f"navigate 额外稳定性检查超时（可能页面仍可用）: {e}")
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def click_personal_settings(self) -> None:
        """点击 personal_settings 按钮"""
        logger.info("点击 personal_settings 按钮")
        self.click(self.PERSONAL_SETTINGS_BUTTON)

    def click_change_password(self) -> None:
        """点击 change_password 按钮"""
        logger.info("点击 change_password 按钮")
        self.click(self.CHANGE_PASSWORD_BUTTON)

    def fill_current_password(self, value: str) -> None:
        """填写 current_password"""
        logger.info("填写 current_password: ***")
        self.secret_fill(self.CURRENT_PASSWORD_INPUT, value)
    
    def get_current_password_value(self) -> str:
        """获取 current_password 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.CURRENT_PASSWORD_INPUT)

    def fill_new_password(self, value: str) -> None:
        """填写 new_password"""
        logger.info("填写 new_password: ***")
        self.secret_fill(self.NEW_PASSWORD_INPUT, value)
    
    def get_new_password_value(self) -> str:
        """获取 new_password 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.NEW_PASSWORD_INPUT)

    def fill_confirm_new_password(self, value: str) -> None:
        """填写 confirm_new_password"""
        logger.info("填写 confirm_new_password: ***")
        self.secret_fill(self.CONFIRM_NEW_PASSWORD_INPUT, value)
    
    def get_confirm_new_password_value(self) -> str:
        """获取 confirm_new_password 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.CONFIRM_NEW_PASSWORD_INPUT)

    def click_toggle_user_menu(self) -> None:
        """点击 toggle_user_menu 按钮"""
        logger.info("点击 toggle_user_menu 按钮")
        self.click(self.TOGGLE_USER_MENU_BUTTON)

    def click_show_password(self) -> None:
        """点击 show_password 按钮"""
        logger.info("点击 show_password 按钮")
        self.click(self.SHOW_PASSWORD_BUTTON)

    def click_save(self) -> None:
        """点击 save 按钮"""
        logger.info("点击 save 按钮")
        self.click(self.SAVE_BUTTON)

    def click_open_next_js_dev_tools(self) -> None:
        """点击 open_next_js_dev_tools 按钮"""
        logger.info("点击 open_next_js_dev_tools 按钮")
        self.click(self.OPEN_NEXT_JS_DEV_TOOLS_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()

    # ═══════════════════════════════════════════════════════════════
    # Compatibility helpers (for tests/admin/profile/change_password/*)
    # ═══════════════════════════════════════════════════════════════

    def clear_form(self) -> None:
        """清空表单（UI 级），用于安全/XSS 等用例避免场景互相污染。"""
        try:
            if self.page.locator(self.CURRENT_PASSWORD_INPUT).count() > 0:
                self.page.fill(self.CURRENT_PASSWORD_INPUT, "")
        except Exception:
            pass
        try:
            if self.page.locator(self.NEW_PASSWORD_INPUT).count() > 0:
                self.page.fill(self.NEW_PASSWORD_INPUT, "")
        except Exception:
            pass
        try:
            if self.page.locator(self.CONFIRM_NEW_PASSWORD_INPUT).count() > 0:
                self.page.fill(self.CONFIRM_NEW_PASSWORD_INPUT, "")
        except Exception:
            pass

    def fill_form(self, current_password: str, new_password: str, confirm_password: str) -> None:
        """
        按 change-password 表单字段填充（增强并发稳定性）
        
        并发健壮性优化：
        - 填充前确保元素可见可交互（避免元素未加载导致填充失败）
        - 填充后验证值是否成功填入（并发时可能被其他事件干扰）
        - 自动重试机制（1次）
        """
        # ✅ 填充前确保元素可交互（避免元素被遮罩/未加载）
        for selector in [self.CURRENT_PASSWORD_INPUT, self.NEW_PASSWORD_INPUT, self.CONFIRM_NEW_PASSWORD_INPUT]:
            try:
                self.page.wait_for_selector(selector, state="visible", timeout=3000)
                # 确保元素可交互（滚动到可见区域）
                self.page.locator(selector).first.scroll_into_view_if_needed(timeout=1000)
            except Exception as e:
                logger.warning(f"fill_form 预检查失败 {selector}: {e}")
        
        # 正常填充
        self.fill_current_password(current_password)
        self.fill_new_password(new_password)
        self.fill_confirm_new_password(confirm_password)
        
        # ✅ 验证填充成功（并发时可能填充失败或被清空）
        try:
            # 给前端一点时间处理 input/change 事件
            self.page.wait_for_timeout(300)
            # 验证 current_password 是否成功填充（使用非空检查避免读取实际值）
            filled_value = self.get_current_password_value()
            if not filled_value or len(filled_value.strip()) == 0:
                logger.warning("fill_form: current_password 未成功填充，重试一次")
                self.fill_current_password(current_password)
                self.page.wait_for_timeout(200)
        except Exception as e:
            logger.warning(f"fill_form 填充验证失败（继续执行）: {e}")

    def submit_change_password(
        self,
        current_password: str,
        new_password: str,
        confirm_password: str,
        *,
        wait_response: bool = True,
        timeout_ms: int = 15000,
    ):
        """
        提交改密（增强并发稳定性）：
        - 默认等待 /api/account/my-profile/change-password 响应并返回 Response
        - 若 wait_response=False：只做提交动作，返回 None（用于 XSS "不得执行"类测试）
        
        并发健壮性优化：
        - 提交前验证表单已填充（避免空表单提交）
        - 增强 expect_response 的容错性
        """
        self.fill_form(current_password=current_password, new_password=new_password, confirm_password=confirm_password)
        
        # ✅ 提交前验证表单已填充（并发时可能填充失败）
        try:
            filled = self.get_current_password_value()
            if not filled or len(filled.strip()) == 0:
                logger.error("submit_change_password: 表单未成功填充，强制重新填充")
                self.fill_form(current_password=current_password, new_password=new_password, confirm_password=confirm_password)
                self.page.wait_for_timeout(500)
        except Exception as e:
            logger.warning(f"submit_change_password 填充验证失败: {e}")
        
        if not wait_response:
            self.click_save()
            return None

        def _match_change_password(resp) -> bool:
            try:
                url = (resp.url or "")
                method = getattr(resp.request, "method", "") or ""
                # 兼容：不同实现可能是 POST/PUT，且 host 可能是 3000（代理）或 44320（直连）
                return (method in {"POST", "PUT"}) and ("/change-password" in url) and ("/api/" in url)
            except Exception:
                return False

        # 经验：全量并发跑时偶发“点击后无请求/监听不到响应”的抖动。
        # 采取“重试一次”的策略：让 P0 更稳，但不掩盖真实失败（仍会返回 None）。
        for attempt in range(2):
            try:
                with self.page.expect_response(_match_change_password, timeout=timeout_ms) as ri:
                    # 确保按钮可点（避免被遮罩/滚动导致 click 不生效）
                    try:
                        self.page.locator(self.SAVE_BUTTON).first.scroll_into_view_if_needed(timeout=1500)
                    except Exception:
                        pass
                    self.click_save()
                return ri.value
            except Exception:
                # 若页面已经出现明显错误提示，就不再盲重试（避免把失败放大）
                try:
                    if self.wait_for_error_hint(timeout_ms=800):
                        break
                except Exception:
                    pass
                if attempt == 0:
                    try:
                        self.page.wait_for_timeout(200)
                    except Exception:
                        pass
                    continue
                break

        # 前端拦截/网络异常/未知路由：返回 None，让上层按“可观测证据”处理
        return None

    def wait_for_error_hint(self, timeout_ms: int = 2000) -> bool:
        """
        等待“可观测失败证据”（toast/field error/alert）。
        不绑定具体文案，仅用于提高断言稳定性。
        """
        selectors = [
            ".invalid-feedback",
            ".text-danger",
            ".validation-summary-errors",
            "span.field-validation-error",
            ".toast-error",
            ".Toastify__toast--error",
            "[role='alert']",
            "p.text-red-500",
        ]
        for sel in selectors:
            try:
                self.page.wait_for_selector(sel, state="visible", timeout=timeout_ms)
                return True
            except Exception:
                continue
        return False

    def get_abp_validation_errors(self, resp) -> List[Dict[str, Any]]:
        """
        解析 ABP 标准错误体里的 validationErrors（若存在）。
        返回 list[dict]，便于上层附加到 Allure。
        """
        if resp is None:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        try:
            err = (data or {}).get("error") or {}
            ves = err.get("validationErrors") or []
            if isinstance(ves, list):
                return ves
        except Exception:
            pass
        return []
