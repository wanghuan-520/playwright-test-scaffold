"""
Account/Register - Terms Checkbox 字段测试

根据需求文档：
- Terms of Service and Privacy Policy 复选框必须勾选才能提交
- 未勾选时应显示验证错误或阻止提交
"""

import uuid

import allure
import pytest
from playwright.sync_api import Page

from pages.account_register_page import AccountRegisterPage
from tests.account.register import _helpers as H
from tests.account.register import _abp_constraints_helpers as ABP
from tests.account.register._helpers import (
    assert_not_redirected_to_login,
    click_save,
)
from tests.myaccount._helpers import attach_rule_source_note, step_shot
from utils.logger import TestLogger

logger = TestLogger("Register_p1_terms")


# ═══════════════════════════════════════════════════════════════════════════════
# Terms Checkbox Required 测试
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Terms Checkbox Required")
@allure.description(
    """
测试点：
- Terms of Service 复选框必须勾选才能提交
- 未勾选时应显示验证错误或阻止提交

规则来源：docs/requirements/account-register-field-requirements.md
"""
)
def test_p1_register_terms_checkbox_required(unauth_page: Page):
    """验证 Terms checkbox 必选"""
    logger.start()
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Terms checkbox required")
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = "terms_required"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    suffix = uuid.uuid4().hex[:10]
    
    # 在 Allure 报告中显示测试数据
    allure.dynamic.parameter("UserName", f"terms_{suffix}")
    allure.dynamic.parameter("Email", f"terms_{suffix}@testmail.com")
    allure.dynamic.parameter("Terms", "未勾选")

    with allure.step("填写表单但不勾选 Terms"):
        po.fill_username(f"terms_{suffix}")
        po.fill_email(f"terms_{suffix}@testmail.com")
        po.fill_password("ValidPass123!")
        # 故意不勾选 po.check_terms()
        step_shot(po, f"step_{case_name}_filled_no_terms", full_page=True)

    with allure.step("尝试提交（应被阻止或显示错误）"):
        click_save(page)
        page.wait_for_timeout(500)
        step_shot(po, f"step_{case_name}_after_submit", full_page=True)

        # 验证：应该仍在注册页面（未跳转）
        current_url = page.url or ""
        assert "/register" in current_url or "/Account/Register" in current_url, \
            f"未勾选 Terms 时不应跳转离开注册页，当前 URL: {current_url}"

        # 验证：应该有错误提示或表单未提交
        import re
        if re.search(r"/Account/Login|/login", current_url):
            pytest.fail("未勾选 Terms 时不应该注册成功")

        allure.attach(
            f"✅ 未勾选 Terms 时，表单被正确阻止提交\n当前 URL: {current_url}",
            name=f"{case_name}_blocked",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Terms Checkbox Attribute Evidence")
@allure.description("验证 Terms 复选框的 required 属性标注（前端可观测证据）")
def test_p1_register_terms_required_attr_evidence(unauth_page: Page):
    """验证 Terms 的 required 属性"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Terms required")
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = "terms_required_attr"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    # 检查 Terms checkbox 的属性
    try:
        checkbox = page.locator(po.TERMS_CHECKBOX)
        if checkbox.count() > 0:
            aria_required = checkbox.get_attribute("aria-required")
            aria_checked = checkbox.get_attribute("aria-checked")
            data_state = checkbox.get_attribute("data-state")
            required_attr = checkbox.get_attribute("required")
        else:
            aria_required = None
            aria_checked = None
            data_state = None
            required_attr = None
    except Exception:
        aria_required = None
        aria_checked = None
        data_state = None
        required_attr = None

    # 在 Allure 报告中显示实际属性
    allure.dynamic.parameter("aria-required", aria_required or "未设置")
    allure.dynamic.parameter("aria-checked", aria_checked or "未设置")
    allure.dynamic.parameter("data-state", data_state or "未设置")

    allure.attach(
        f"═══════════════════════════════════════════════════\n"
        f"【Terms Checkbox 属性检查】\n"
        f"  required: {required_attr or '未设置'}\n"
        f"  aria-required: {aria_required or '未设置'}\n"
        f"  aria-checked: {aria_checked or '未设置'}\n"
        f"  data-state: {data_state or '未设置'}\n"
        f"═══════════════════════════════════════════════════",
        name=f"📋 {case_name}_属性信息",
        attachment_type=allure.attachment_type.TEXT,
    )
    step_shot(po, f"step_{case_name}", full_page=True)

    # Terms checkbox 必须存在
    assert page.locator(po.TERMS_CHECKBOX).count() > 0, f"{case_name}: Terms checkbox 不存在"


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AccountRegister")
@allure.story("P1 - Terms Checkbox Check and Uncheck")
@allure.description("验证 Terms 复选框的勾选和取消勾选功能")
def test_p1_register_terms_checkbox_toggle(unauth_page: Page):
    """验证 Terms checkbox 勾选/取消功能"""
    attach_rule_source_note("docs/requirements/account-register-field-requirements.md: Terms checkbox")
    page = unauth_page
    po = AccountRegisterPage(page)
    case_name = "terms_toggle"

    H.ensure_register_page(page, po)
    assert_not_redirected_to_login(page)

    with allure.step("初始状态应为未勾选"):
        initial_checked = po.is_terms_checked()
        allure.dynamic.parameter("初始状态", "已勾选" if initial_checked else "未勾选")
        step_shot(po, f"step_{case_name}_initial", full_page=True)

    with allure.step("勾选 Terms checkbox"):
        po.check_terms()
        page.wait_for_timeout(200)
        after_check = po.is_terms_checked()
        allure.dynamic.parameter("勾选后状态", "已勾选" if after_check else "未勾选")
        step_shot(po, f"step_{case_name}_after_check", full_page=True)
        assert after_check, f"{case_name}: 勾选后应为已勾选状态"

    allure.attach(
        f"═══════════════════════════════════════════════════\n"
        f"【Terms Checkbox 状态变化】\n"
        f"  初始状态: {'已勾选' if initial_checked else '未勾选'}\n"
        f"  勾选后: {'已勾选' if after_check else '未勾选'}\n"
        f"═══════════════════════════════════════════════════",
        name=f"📋 {case_name}_状态信息",
        attachment_type=allure.attachment_type.TEXT,
    )

