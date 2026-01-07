# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# AdminSettings - P0
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_settings_page import AdminSettingsPage
from tests.admin.settings._helpers import (
    FIELD_RULES,
    assert_not_redirected_to_login,
    assert_any_validation_evidence,
    assert_toast_contains_any,
    click_save,
    has_any_error_ui,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger('settings_settings' + "_p0")


@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AdminSettings')
@allure.story("P0")
@allure.title("页面加载")
def test_p0_page_load(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminSettingsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    po.take_screenshot('settings_settings' + "_p0_page_load", full_page=True)
    logger.end(success=True)




@pytest.mark.P0
@pytest.mark.functional
@allure.feature('AdminSettings')
@allure.story('P0')
@allure.title('主流程：修改并保存（带回滚）')
def test_p0_happy_path_update_save_with_rollback(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminSettingsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selector = 'role=textbox[name="Default from address"]'
    if page.locator(selector).count() == 0:
        pytest.skip('字段不可见/不存在（页面结构变化或 selector 失效）')

    snap = snapshot_inputs(page, FIELD_RULES)
    original = page.input_value(selector)
    new_value = (original or 'QA') + 'X'

    try:
        with allure.step('修改字段并保存'):
            page.fill(selector, new_value)
            po.take_screenshot('settings_settings' + '_p0_before_save')
            click_save(page)
            resp = wait_mutation_response(page, timeout_ms=60000)
            assert_not_redirected_to_login(page)
            if resp is not None:
                assert resp.status < 500, f'unexpected api status: {resp.status}'
            assert not has_any_error_ui(page), 'unexpected error UI after save'
            po.take_screenshot('settings_settings' + '_p0_after_save')
    finally:
        with allure.step('回滚（UI 级恢复）'):
            restore_inputs(page, snap)
            click_save(page)
            _ = wait_mutation_response(page, timeout_ms=60000)
            po.take_screenshot('settings_settings' + '_p0_after_rollback')

    logger.end(success=True)


