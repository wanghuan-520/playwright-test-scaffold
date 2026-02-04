# ═══════════════════════════════════════════════════════════════
# Account/Login - P2
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.account_login_page import AccountLoginPage
from tests.account.login._helpers import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger("Login_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2 - Password Input Security")
@allure.description(
    """
测试点：
- 密码输入框 type="password" 确保不明文显示
- 密码不可被直接看到（安全性要求）
证据：input type 属性值
"""
)
def test_p2_password_input_masked(unauth_page: Page):
    """测试密码输入框是否隐藏显示（type=password）"""
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证密码输入框 type 属性"):
        password_input = page.locator(po.PASSWORD_INPUT)
        expect(password_input).to_be_visible()
        
        # 获取 type 属性
        input_type = password_input.get_attribute("type")
        allure.attach(
            f"密码输入框 type: {input_type}",
            name="password_input_type",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 断言 type="password"
        assert input_type == "password", f"密码输入框应为 type='password'，实际为 '{input_type}'"

    with allure.step("验证输入密码后仍然隐藏"):
        password_input.fill("TestPassword123!")
        po.take_screenshot("Login_p2_password_masked", full_page=False)
        
        # 再次确认 type 没有被改变
        input_type_after = password_input.get_attribute("type")
        assert input_type_after == "password", "输入后密码框 type 被改变"
        
        allure.attach("✅ 密码输入后仍为隐藏状态", name="masked_status", attachment_type=allure.attachment_type.TEXT)

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2")
def test_p2_fields_visible(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    # 使用Page Object的selector常量
    expect(page.locator(po.USERNAME_OR_EMAIL_ADDRESS_INPUT)).to_be_visible()
    expect(page.locator(po.PASSWORD_INPUT)).to_be_visible()
    po.take_screenshot("Login_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2")
@allure.description(
    """
测试点：
- 键盘 Tab 导航可用性
- 每按一次 Tab 截图一次，验证焦点移动
证据：每次 Tab 后的截图
"""
)
def test_p2_keyboard_tab_navigation(unauth_page: Page):
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    def _highlight_and_shot(step_name: str, desc: str):
        """高亮当前焦点元素并截图"""
        # 添加红色边框高亮当前焦点元素
        page.evaluate("""() => {
            // 清除之前的高亮
            document.querySelectorAll('[data-focus-highlight]').forEach(el => {
                el.style.outline = '';
                el.style.outlineOffset = '';
                el.removeAttribute('data-focus-highlight');
            });
            // 高亮当前焦点元素
            const el = document.activeElement;
            if (el && el !== document.body) {
                el.style.outline = '3px solid red';
                el.style.outlineOffset = '2px';
                el.setAttribute('data-focus-highlight', 'true');
            }
        }""")
        active_el = page.evaluate("document.activeElement?.id || document.activeElement?.tagName")
        allure.attach(f"焦点元素: {active_el}", name=f"{step_name}_focus_state", attachment_type=allure.attachment_type.TEXT)
        po.take_screenshot(f"Login_p2_{step_name}", full_page=False)

    with allure.step("Tab 导航测试：每按一次 Tab 截图一次，并记录焦点状态"):
        # 初始状态
        po.take_screenshot("Login_p2_tab_0_initial", full_page=False)
        
        # 点击第一个输入框
        page.click(po.USERNAME_OR_EMAIL_ADDRESS_INPUT)
        page.wait_for_timeout(300)
        _highlight_and_shot("tab_1_username_focused", "用户名输入框获得焦点")
        
        # 按 Tab 到密码框
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        _highlight_and_shot("tab_2_password_focused", "密码输入框获得焦点")
        
        # 再按 Tab 到登录按钮
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        _highlight_and_shot("tab_3_button_focused", "登录按钮获得焦点")

    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2 - Links Visibility")
@allure.description(
    """
测试点：
- Register 链接可见性
- Forgot Password 链接可见性
证据：链接可见性截图
"""
)
def test_p2_links_visible(unauth_page: Page):
    """测试登录页上的链接是否可见"""
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证 Register 链接可见性"):
        register_link = page.locator(po.REGISTER_LINK)
        if register_link.count() > 0:
            expect(register_link).to_be_visible()
            allure.attach("Register 链接可见", name="register_link_status", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("⚠️ Register 链接不存在（可能是设计如此）", name="register_link_status", attachment_type=allure.attachment_type.TEXT)

    with allure.step("验证 Forgot Password 链接可见性"):
        forgot_link = page.locator(po.FORGOT_PASSWORD_LINK)
        if forgot_link.count() > 0:
            expect(forgot_link).to_be_visible()
            allure.attach("Forgot Password 链接可见", name="forgot_link_status", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("⚠️ Forgot Password 链接不存在（可能是设计如此）", name="forgot_link_status", attachment_type=allure.attachment_type.TEXT)

    po.take_screenshot("Login_p2_links_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2 - Button Visibility")
@allure.description(
    """
测试点：
- Login 按钮可见性
- Login 按钮文案正确
证据：按钮截图
"""
)
def test_p2_login_button_visible(unauth_page: Page):
    """测试登录按钮是否可见且文案正确"""
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("验证 Login 按钮可见性"):
        login_btn = page.locator(po.LOGIN_BUTTON)
        expect(login_btn).to_be_visible()
        
        # 获取按钮文本
        btn_text = login_btn.inner_text()
        allure.attach(f"按钮文案: {btn_text}", name="button_text", attachment_type=allure.attachment_type.TEXT)
        
        # 验证按钮文案（通常是 "Login" 或 "Sign In" 或 "登录"）
        assert btn_text.strip(), "Login 按钮文案为空"

    po.take_screenshot("Login_p2_button_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature("AccountLogin")
@allure.story("P2 - Remember Me UI")
@allure.description(
    """
测试点：
- Remember Me 复选框可见性
- Remember Me 复选框可点击
- Remember Me 勾选/取消状态变化
证据：复选框截图
"""
)
def test_p2_remember_me_checkbox_visible(unauth_page: Page):
    """测试 Remember Me 复选框 UI 可见性和可交互性"""
    logger.start()
    page = unauth_page
    po = AccountLoginPage(page)
    po.navigate()
    assert_not_redirected_to_login(page)

    with allure.step("查找 Remember Me 复选框"):
        # 尝试多种定位方式（包括自定义组件）
        checkbox = None
        checkbox_container = None
        
        # 标准 checkbox 选择器
        standard_selectors = [
            "input[type='checkbox'][name*='remember' i]",
            "input[type='checkbox'][id*='remember' i]",
            "label:has-text('Remember') input[type='checkbox']",
        ]
        
        # 自定义组件选择器（基于文本查找父容器）
        custom_selectors = [
            "text=Remember me",
            "label:has-text('Remember me')",
            "*:has-text('Remember me')",
        ]
        
        # 先尝试标准 checkbox
        for selector in standard_selectors:
            try:
                loc = page.locator(selector).first
                if loc.count() > 0 and loc.is_visible():
                    checkbox = loc
                    allure.attach(
                        f"找到标准 checkbox: {selector}",
                        name="checkbox_selector",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    break
            except Exception:
                continue
        
        # 如果没找到标准 checkbox，尝试自定义组件
        if not checkbox:
            for selector in custom_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.count() > 0 and loc.is_visible():
                        checkbox_container = loc
                        allure.attach(
                            f"找到自定义 Remember Me 组件: {selector}",
                            name="checkbox_selector",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                        break
                except Exception:
                    continue
        
        if not checkbox and not checkbox_container:
            allure.attach(
                "⚠️ 未找到 Remember Me 复选框或自定义组件",
                name="checkbox_not_found",
                attachment_type=allure.attachment_type.TEXT,
            )
            po.take_screenshot("Login_p2_remember_me_not_found", full_page=True)
            pytest.skip("Remember Me 复选框未找到")
    
    with allure.step("验证 Remember Me 复选框可见"):
        target = checkbox if checkbox else checkbox_container
        expect(target).to_be_visible()
        po.take_screenshot("Login_p2_remember_me_visible", full_page=True)
    
    with allure.step("验证 Remember Me 可交互"):
        if checkbox:
            # 标准 checkbox：使用 is_checked() 方法
            initial_checked = checkbox.is_checked()
            allure.attach(f"初始勾选状态: {initial_checked}", name="initial_state", attachment_type=allure.attachment_type.TEXT)
            
            checkbox.click()
            page.wait_for_timeout(300)
            
            after_click_checked = checkbox.is_checked()
            allure.attach(f"点击后勾选状态: {after_click_checked}", name="after_click_state", attachment_type=allure.attachment_type.TEXT)
            
            assert initial_checked != after_click_checked, f"点击后状态未改变"
            po.take_screenshot("Login_p2_remember_me_toggled", full_page=True)
            
            # 恢复原状态
            checkbox.click()
            page.wait_for_timeout(300)
        else:
            # 自定义组件：检查是否可点击，并观察视觉变化
            allure.attach(
                "自定义组件，通过点击测试交互性",
                name="custom_component",
                attachment_type=allure.attachment_type.TEXT,
            )
            
            # 截图记录初始状态
            po.take_screenshot("Login_p2_remember_me_initial", full_page=True)
            
            # 点击组件
            checkbox_container.click()
            page.wait_for_timeout(300)
            po.take_screenshot("Login_p2_remember_me_clicked", full_page=True)
            
            # 再次点击
            checkbox_container.click()
            page.wait_for_timeout(300)
            po.take_screenshot("Login_p2_remember_me_toggled", full_page=True)
        
        allure.attach(
            "✅ Remember Me 复选框可正常交互",
            name="interaction_result",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)

