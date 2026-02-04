# ═══════════════════════════════════════════════════════════════
# Personal Settings Page Object
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
Personal Settings（个人设置）页面对象。

说明：
- 该页面路由为 /account/profile
- 需要登录后才能访问
- 编辑模式：点击 Edit 按钮后进入编辑状态
"""

import os
import re
from typing import Dict, Optional
import time

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class PersonalSettingsPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # CONFIG
    # ═══════════════════════════════════════════════════════════════

    URL = "/account/profile"

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS (Playwright MCP 定位)
    # ═══════════════════════════════════════════════════════════════

    # 页面标题
    PAGE_TITLE = 'h1:has-text("My Account")'
    PROFILE_HEADING = 'h2:has-text("Profile")'
    
    # 导航
    BACK_BUTTON = 'button:has-text("Back")'
    PROFILE_LINK = 'a[href="/account/profile"]'
    PASSWORD_LINK = 'a[href="/account/password"]'
    
    # 编辑模式按钮
    EDIT_BUTTON = 'button:has-text("Edit")'
    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'
    
    # 查看模式下的字段显示（paragraph）
    VIEW_USERNAME = 'p:near(p:text("User Name"))'
    VIEW_FULLNAME = 'p:near(p:text("Full Name"))'
    VIEW_EMAIL = 'p:near(p:text("Email Address"))'
    VIEW_PHONE = 'p:near(p:text("Phone Number"))'
    
    # 编辑模式下的输入框
    # User Name 和 Email 是 disabled 的
    USERNAME_INPUT = 'input[disabled]:near(:text("User Name"))'
    FIRST_NAME_INPUT = 'input:near(:text("First Name"))'
    LAST_NAME_INPUT = 'input:near(:text("Last Name"))'
    EMAIL_INPUT = 'input[disabled]:near(:text("Email Address"))'
    PHONE_INPUT = 'input:near(:text("Phone Number"))'
    
    # 更精确的选择器（使用 role）
    USERNAME_INPUT_ROLE = 'textbox >> nth=0'  # First disabled textbox (username)
    FIRST_NAME_INPUT_ROLE = 'textbox >> nth=1'  # Second textbox (first name)
    LAST_NAME_INPUT_ROLE = 'textbox >> nth=2'  # Third textbox (last name)
    EMAIL_INPUT_ROLE = 'textbox >> nth=3'  # Fourth disabled textbox (email)
    PHONE_INPUT_ROLE = 'textbox >> nth=4'  # Fifth textbox (phone)
    
    # Security Settings
    CHANGE_PASSWORD_BUTTON = 'button:has-text("Change")'
    
    # Avatar
    AVATAR_BUTTON = 'button:has(img):near(h4)'  # 头像按钮（Personal Information 区域）
    AVATAR_DIALOG = 'dialog, [role="dialog"]'
    AVATAR_DIALOG_TITLE = 'h2:has-text("Upload Avatar")'
    AVATAR_DROP_ZONE = 'p:has-text("Drag and drop")'
    AVATAR_CANCEL_BUTTON = 'button:has-text("Cancel")'
    AVATAR_SAVE_BUTTON = 'button:has-text("Save Avatar")'  # 裁剪后保存按钮
    AVATAR_IMAGE = 'button:has(img):near(h4) img'  # 头像图片
    
    # Toast messages
    SUCCESS_TOAST_TEXT = "Profile updated successfully"
    AVATAR_SUCCESS_TOAST = "Avatar updated"

    # 页面加载指示器
    page_loaded_indicator = 'h2:has-text("Profile")'

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    def navigate(self) -> None:
        """导航到 Personal Settings 页面"""
        logger.info(f"导航到 Personal Settings: {self.URL}")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            # 检查 Profile 标题是否可见
            if self.is_visible(self.PROFILE_HEADING, timeout=3000):
                return True
            # 或检查编辑按钮是否可见
            if self.is_visible(self.EDIT_BUTTON, timeout=1500):
                return True
            return False
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # EDIT MODE
    # ═══════════════════════════════════════════════════════════════

    def is_in_edit_mode(self) -> bool:
        """检查是否处于编辑模式"""
        try:
            return self.is_visible(self.SAVE_BUTTON, timeout=1000)
        except Exception:
            return False

    def enter_edit_mode(self) -> None:
        """进入编辑模式"""
        if not self.is_in_edit_mode():
            logger.info("点击 Edit 按钮进入编辑模式")
            self.click(self.EDIT_BUTTON)
            self.page.wait_for_timeout(500)

    def exit_edit_mode(self) -> None:
        """退出编辑模式（不保存）"""
        if self.is_in_edit_mode():
            logger.info("点击 Cancel 按钮退出编辑模式")
            self.click(self.CANCEL_BUTTON)
            self.page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # FORM OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def _get_input_by_label(self, label_text: str) -> Optional[str]:
        """根据标签文本获取输入框的值"""
        try:
            # 找到标签后面的输入框
            locator = self.page.locator(f'input:near(:text("{label_text}"))').first
            if locator.is_visible(timeout=1000):
                return locator.input_value()
        except Exception:
            pass
        return None

    def _fill_input_by_label(self, label_text: str, value: str) -> None:
        """根据标签文本填写输入框"""
        try:
            locator = self.page.locator(f'input:near(:text("{label_text}"))').first
            locator.fill(value)
        except Exception as e:
            logger.warning(f"无法填写 {label_text}: {e}")

    def read_form_values(self) -> Dict[str, str]:
        """读取表单当前值（需要先进入编辑模式）"""
        self.enter_edit_mode()
        
        values = {}
        try:
            # 使用 nth 索引定位输入框
            textboxes = self.page.get_by_role('textbox')
            count = textboxes.count()
            
            if count >= 1:
                values["userName"] = textboxes.nth(0).input_value()
            if count >= 2:
                values["firstName"] = textboxes.nth(1).input_value()
            if count >= 3:
                values["lastName"] = textboxes.nth(2).input_value()
            if count >= 4:
                values["email"] = textboxes.nth(3).input_value()
            if count >= 5:
                values["phoneNumber"] = textboxes.nth(4).input_value()
        except Exception as e:
            logger.warning(f"读取表单值失败: {e}")
        
        return values

    def fill_form(self, values: Dict[str, str]) -> None:
        """填写表单（只更新传入字段，需要先进入编辑模式）"""
        self.enter_edit_mode()
        
        textboxes = self.page.get_by_role('textbox')
        
        # firstName -> 第2个输入框 (index 1)
        if "firstName" in values:
            try:
                textboxes.nth(1).fill(values["firstName"])
            except Exception as e:
                logger.warning(f"无法填写 firstName: {e}")
        
        # lastName -> 第3个输入框 (index 2)
        if "lastName" in values:
            try:
                textboxes.nth(2).fill(values["lastName"])
            except Exception as e:
                logger.warning(f"无法填写 lastName: {e}")
        
        # phoneNumber -> 第5个输入框 (index 4)
        if "phoneNumber" in values:
            try:
                textboxes.nth(4).fill(values["phoneNumber"])
            except Exception as e:
                logger.warning(f"无法填写 phoneNumber: {e}")
        
        # 给 React 状态一个刷新窗口
        self.page.wait_for_timeout(50)

    def fill_first_name(self, value: str) -> None:
        """填写 First Name"""
        self.enter_edit_mode()
        self.page.get_by_role('textbox').nth(1).fill(value)

    def fill_last_name(self, value: str) -> None:
        """填写 Last Name"""
        self.enter_edit_mode()
        self.page.get_by_role('textbox').nth(2).fill(value)

    def fill_phone(self, value: str) -> None:
        """填写 Phone Number"""
        self.enter_edit_mode()
        self.page.get_by_role('textbox').nth(4).fill(value)

    def click_save(self) -> None:
        """点击保存"""
        logger.info("点击 Save 按钮")
        self.click(self.SAVE_BUTTON)

    def click_cancel(self) -> None:
        """点击取消"""
        logger.info("点击 Cancel 按钮")
        self.click(self.CANCEL_BUTTON)

    # ═══════════════════════════════════════════════════════════════
    # NETWORK-AWARE SAVE
    # ═══════════════════════════════════════════════════════════════

    def save_and_wait_profile_update(self, timeout_ms: int = 15000):
        """
        点击 Save 并等待后端 profile 更新请求返回。
        """
        def _match(resp):
            try:
                url = resp.url or ""
                method = resp.request.method
                # 匹配 profile 更新 API（包括 /api/vibe/my-profile）
                return (
                    ("/api/vibe/my-profile" in url or "/api/account/my-profile" in url or "/api/account/profile" in url or "/api/user" in url)
                    and method in ("PUT", "POST", "PATCH")
                )
            except Exception:
                return False

        with self.page.expect_response(_match, timeout=timeout_ms) as resp_info:
            self.click_save()

        resp = resp_info.value
        try:
            if resp is not None and resp.ok:
                setattr(self, "_profile_update_ok_in_test", True)
        except Exception:
            pass
        return resp

    def click_save_and_capture_profile_update(self, timeout_ms: int = 3000):
        """
        点击 Save，并尽力捕获 profile 更新响应。
        若前端校验拦截导致不发请求：返回 None
        """
        def _match(resp):
            try:
                url = resp.url or ""
                method = resp.request.method
                # 匹配 profile 更新 API（包括 /api/vibe/my-profile）
                return (
                    ("/api/vibe/my-profile" in url or "/api/account/my-profile" in url or "/api/account/profile" in url or "/api/user" in url)
                    and method in ("PUT", "POST", "PATCH")
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

    def wait_for_save_success(self, timeout_ms: int = 8000) -> None:
        """等待保存成功提示"""
        try:
            self.page.wait_for_selector(f"text={self.SUCCESS_TOAST_TEXT}", state="visible", timeout=timeout_ms)
            return
        except Exception:
            pass

        # 兜底：等 role=status 或 alert 出现
        try:
            status = self.page.get_by_role("status")
            status.wait_for(state="visible", timeout=timeout_ms)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION HELPERS
    # ═══════════════════════════════════════════════════════════════

    def click_back(self) -> None:
        """点击返回按钮"""
        logger.info("点击 Back 按钮")
        self.click(self.BACK_BUTTON)

    def go_to_password_page(self) -> None:
        """导航到修改密码页面"""
        logger.info("点击 Password 链接")
        self.click(self.PASSWORD_LINK)

    def click_change_password(self) -> None:
        """点击修改密码按钮"""
        logger.info("点击 Change Password 按钮")
        self.click(self.CHANGE_PASSWORD_BUTTON)

    # ═══════════════════════════════════════════════════════════════
    # AVATAR OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def open_avatar_dialog(self) -> None:
        """打开头像上传弹窗"""
        logger.info("点击头像按钮打开上传弹窗")
        # 头像按钮是一个没有文本的按钮（只包含图片）
        # 使用 Playwright 的 filter 方法匹配空文本按钮
        avatar_btn = self.page.get_by_role('button').filter(has_text=re.compile(r'^$')).first
        avatar_btn.click()
        self.page.wait_for_selector(self.AVATAR_DIALOG, state="visible", timeout=5000)

    def is_avatar_dialog_open(self) -> bool:
        """检查头像上传弹窗是否打开"""
        try:
            return self.is_visible(self.AVATAR_DIALOG_TITLE, timeout=1000)
        except Exception:
            return False

    def close_avatar_dialog(self) -> None:
        """关闭头像上传弹窗"""
        if self.is_avatar_dialog_open():
            logger.info("关闭头像上传弹窗")
            self.click(self.AVATAR_CANCEL_BUTTON)
            self.wait_for_avatar_dialog_closed()

    def wait_for_avatar_dialog_closed(self, timeout_ms: int = 5000) -> None:
        """等待头像弹窗完全关闭"""
        try:
            self.page.wait_for_selector(self.AVATAR_DIALOG_TITLE, state="hidden", timeout=timeout_ms)
        except Exception:
            pass
        # 额外等待动画完成
        self.page.wait_for_timeout(500)

    def upload_avatar(self, file_path: str, auto_save: bool = True) -> None:
        """
        上传头像图片。
        
        Args:
            file_path: 图片文件的绝对路径
            auto_save: 是否自动点击 "Save Avatar" 按钮（默认 True）
        """
        logger.info(f"上传头像: {file_path}")
        
        # 打开上传弹窗（如果没打开）
        if not self.is_avatar_dialog_open():
            self.open_avatar_dialog()
        
        # 等待 file input 出现（可能是隐藏的）
        # 触发文件选择
        with self.page.expect_file_chooser() as fc_info:
            # 点击 drop zone 区域触发文件选择
            drop_zone = self.page.locator(self.AVATAR_DROP_ZONE)
            drop_zone.click()
        
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        logger.info("文件已选择")
        
        # 等待裁剪界面出现
        self.page.wait_for_timeout(500)
        
        if auto_save:
            # 点击 "Save Avatar" 按钮保存
            self.click_save_avatar()

    def click_save_avatar(self, wait_for_network: bool = True) -> None:
        """
        点击 'Save Avatar' 按钮保存裁剪后的头像
        
        Args:
            wait_for_network: 是否等待网络请求完成（对大文件上传很重要）
        """
        logger.info("点击 Save Avatar 按钮")
        try:
            save_btn = self.page.locator(self.AVATAR_SAVE_BUTTON)
            save_btn.wait_for(state="visible", timeout=5000)
            
            if wait_for_network:
                # 等待网络请求完成，确保大文件上传成功
                with self.page.expect_response(
                    lambda resp: "avatar" in resp.url.lower() or "upload" in resp.url.lower() or "profile" in resp.url.lower(),
                    timeout=60000  # 大文件可能需要更长时间
                ) as response_info:
                    save_btn.click()
                    logger.info("已点击 Save Avatar，等待上传完成...")
                
                response = response_info.value
                logger.info(f"上传响应: status={response.status}, url={response.url}")
            else:
                save_btn.click()
                logger.info("已点击 Save Avatar")
        except Exception as e:
            logger.warning(f"Save Avatar 按钮不可见或点击失败: {e}")

    def get_avatar_src(self) -> Optional[str]:
        """获取当前头像的 src 属性"""
        try:
            img = self.page.locator(self.AVATAR_IMAGE).first
            if img.is_visible(timeout=2000):
                return img.get_attribute("src")
        except Exception:
            pass
        return None

    def wait_for_avatar_upload_success(self, timeout_ms: int = 10000) -> bool:
        """等待头像上传成功"""
        try:
            # 方式1：等待弹窗关闭
            self.page.wait_for_selector(self.AVATAR_DIALOG, state="hidden", timeout=timeout_ms)
            return True
        except Exception:
            pass
        
        try:
            # 方式2：等待成功 toast
            self.page.wait_for_selector(f"text={self.AVATAR_SUCCESS_TOAST}", state="visible", timeout=timeout_ms)
            return True
        except Exception:
            pass
        
        return False

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def is_login_page(self) -> bool:
        """检查是否被重定向到了登录页"""
        url = (self.page.url or "").lower()
        return "/login" in url

    def _toast_locator(self):
        """Toast/notification 容器选择器"""
        return self.page.locator(
            ",".join([
                    ".Toastify__toast",
                    ".toast",
                    "[role='alert']",
                    "[role='status']",
                    ".ant-message-notice",
            ])
        )

    def wait_for_toasts_to_disappear(self, timeout_ms: int = 8000) -> None:
        """等待 toast 消失"""
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

    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        errors = []
        try:
            # 查找错误文案
            error_selectors = [
                ".text-red-500",
                ".text-danger",
                ".error-message",
                "[role='alert']",
            ]
            for sel in error_selectors:
                elements = self.page.locator(sel)
                count = elements.count()
                for i in range(count):
                    text = elements.nth(i).text_content()
                    if text:
                        errors.append(text.strip())
        except Exception:
            pass
        return errors

    def take_element_screenshot(self, selector: str, name: str = "element_screenshot") -> str:
        """截取元素局部截图"""
        from pathlib import Path
        from datetime import datetime
        import allure

        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = screenshot_dir / filename

        try:
            self.page.eval_on_selector(selector, "el => el.scrollIntoView({block: 'center'})")
        except Exception:
            pass

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
                    "el => { if (el.__qa_prev_outline !== undefined) { el.style.outline = el.__qa_prev_outline; } }",
                )
            except Exception:
                pass

        with open(filepath, "wb") as f:
            f.write(shot)

        allure.attach(shot, name=name, attachment_type=allure.attachment_type.PNG)
        logger.info(f"元素截图已保存: {filepath}")
        return str(filepath)
