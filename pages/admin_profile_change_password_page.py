# ═══════════════════════════════════════════════════════════════
# AdminProfileChangePassword Page Object
# Updated: 2026-02-03 - Adapted for Sisyphus Research Platform
# ═══════════════════════════════════════════════════════════════
"""
Change Password 页面对象
URL: /account/password
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
    Change Password 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    适配：Sisyphus Research Platform - /account/password
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS (Updated for Sisyphus Research Platform)
    # ═══════════════════════════════════════════════════════════════
    
    # 侧边栏导航
    PROFILE_LINK = 'a[href="/account/profile"]'
    PASSWORD_LINK = 'a[href="/account/password"]'
    BACK_BUTTON = 'button:has-text("Back")'

    # current_password | placeholder: Enter current password
    CURRENT_PASSWORD_INPUT = 'input[placeholder="Enter current password"]'

    # new_password | placeholder: Enter new password
    NEW_PASSWORD_INPUT = 'input[placeholder="Enter new password"]'

    # confirm_new_password | placeholder: Confirm new password
    CONFIRM_NEW_PASSWORD_INPUT = 'input[placeholder="Confirm new password"]'

    # 密码可见性切换按钮（每个输入框旁边都有）
    SHOW_PASSWORD_BUTTONS = 'button:has(img[alt=""])'

    # save/submit button
    SAVE_BUTTON = 'button:has-text("Update Password")'

    # 页面标题
    PAGE_TITLE = 'h2:has-text("Change Password")'
    
    URL = '/account/password'
    page_loaded_indicator = SAVE_BUTTON

    # 后端 API（用于等待/取证）
    CHANGE_PASSWORD_API = "/api/vibe/change-password"

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
        logger.info(f"导航到 Change Password 页面: {self.URL}")
        self.goto(self.URL)
        self.wait_for_page_load()
        
        # ✅ 并发健壮性：确保关键表单元素完全可用
        try:
            self.page.wait_for_selector(self.CURRENT_PASSWORD_INPUT, state="visible", timeout=8000)
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
        - 每个字段填充后小延迟确保前端状态更新
        """
        # ✅ 填充前确保元素可交互（避免元素被遮罩/未加载）
        for selector in [self.CURRENT_PASSWORD_INPUT, self.NEW_PASSWORD_INPUT, self.CONFIRM_NEW_PASSWORD_INPUT]:
            try:
                self.page.wait_for_selector(selector, state="visible", timeout=5000)
                # 确保元素可交互（滚动到可见区域）
                self.page.locator(selector).first.scroll_into_view_if_needed(timeout=1000)
            except Exception as e:
                logger.warning(f"fill_form 预检查失败 {selector}: {e}")
        
        # 正常填充，每个字段后短暂等待确保前端处理完成
        self.fill_current_password(current_password)
        self.page.wait_for_timeout(100)
        self.fill_new_password(new_password)
        self.page.wait_for_timeout(100)
        self.fill_confirm_new_password(confirm_password)
        self.page.wait_for_timeout(200)  # 最后等待前端状态同步

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
        
        if not wait_response:
            self.click_save()
            return None

        def _match_change_password(resp) -> bool:
            try:
                url = (resp.url or "")
                method = getattr(resp.request, "method", "") or ""
                # 兼容：POST /api/vibe/change-password
                return (method == "POST") and ("/change-password" in url) and ("/api/" in url)
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
        等待"可观测失败证据"（toast/field error/alert）。
        不绑定具体文案，仅用于提高断言稳定性。
        """
        selectors = [
            # Toast in Notifications region (Sonner/Radix style)
            "li:has(button:has-text('Dismiss'))",
            "[role='region'] li",
            "ol li:has(button)",
            # Common error indicators
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
                loc = self.page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=timeout_ms // len(selectors)):
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
