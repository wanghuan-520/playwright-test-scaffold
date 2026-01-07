# ═══════════════════════════════════════════════════════════════
# GENERATED FILE - DO NOT EDIT BY HAND
# rules_context: reports/rules_context.md
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# Admin - P0
# Generated: 2025-12-24 23:51:39
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.admin_page import AdminPage
from tests.admin.admin._helpers import (
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

logger = TestLogger('admin' + "_p0")


@pytest.mark.P0
@pytest.mark.functional
@allure.feature('Admin')
@allure.story("P0")
@allure.title("页面加载")
def test_p0_page_load(auth_page: Page):
    logger.start()
    page = auth_page
    po = AdminPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    po.take_screenshot('admin' + "_p0_page_load", full_page=True)
    logger.end(success=True)




