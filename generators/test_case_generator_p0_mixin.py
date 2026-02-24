"""
TestCaseGenerator P0 template builder.
"""

from __future__ import annotations

from typing import Dict, List

from generators.page_types import PageInfo
from generators.utils import get_file_name_from_url, get_page_name_from_url, to_class_name, to_snake_case


class TestCaseGeneratorP0Mixin:
    def _p0_py(
        self,
        page_info: PageInfo,
        module: str,
        page: str,
        page_key: str,
        rules: List[Dict],
        *,
        is_change_password: bool,
    ) -> str:
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        file_name = get_file_name_from_url(page_info.url)
        helper_mod = f"tests.{module}.{page}._helpers"

        required_rules = [r for r in (rules or []) if r.get("required") is True and r.get("selector")]
        first_rule = next(
            (
                r
                for r in (rules or [])
                if r.get("selector")
                and str((r.get("html_type") or "")).strip().lower() not in {"password"}
            ),
            None,
        )
        happy_sel = (first_rule or {}).get("selector", "")

        required_block = ""
        if required_rules:
            blocks: List[str] = []
            for r in required_rules:
                src_comment = self._render_sources_comment(r)
                field = r.get("field") or "field"
                sel = r.get("selector")
                blocks.append(
                    f"\n\n{src_comment}\n"
                    f"@pytest.mark.P0\n"
                    f"@pytest.mark.validation\n"
                    f"@allure.feature({class_name!r})\n"
                    f"@allure.story('P0')\n"
                    f"@allure.title('必填校验：{field}')\n"
                    f"def test_p0_required_{to_snake_case(field)}(auth_page: Page):\n"
                    f"    logger.start()\n"
                    f"    page = auth_page\n"
                    f"    po = {class_name}Page(page)\n\n"
                    f"    po.navigate()\n"
                    f"    assert_not_redirected_to_login(page)\n\n"
                    f"    selector = {sel!r}\n"
                    f"    if page.locator(selector).count() == 0:\n"
                    f"        pytest.skip('字段不可见/不存在（页面结构变化或 selector 失效）')\n\n"
                    f"    original = page.input_value(selector)\n"
                    f"    page.fill(selector, '')\n"
                    f"    click_save(page)\n"
                    f"    assert_any_validation_evidence(page, selector)\n"
                    f"    po.take_screenshot('{page_key}_p0_required_{to_snake_case(field)}')\n\n"
                    f"    page.fill(selector, original)\n"
                    f"    # 必填校验用例不应产生持久化副作用：恢复输入即可，不再次提交。\n"
                    f"    logger.end(success=True)\n"
                )
            required_block = "".join(blocks)

        change_password_p0 = ""
        if is_change_password:
            change_password_p0 = (
                f"\n\n@pytest.mark.P0\n"
                f"@pytest.mark.functional\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P0')\n"
                f"@allure.title('前端必拦截：新密码与确认密码不一致')\n"
                f"def test_p0_new_confirm_mismatch_blocks_submit(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    # 不依赖真实旧密码：只验证“前端一致性校验”与可检证证据（toast）\n"
                f"    po.fill_currentpassword('wrong-current-123')\n"
                f"    po.fill_newpassword('NewPass_123')\n"
                f"    po.fill_confirmnewpassword('NewPass_124')\n"
                f"    click_save(page)\n"
                f"    assert_not_redirected_to_login(page)\n"
                f"    assert_toast_contains_any(page, ['Confirm', '确认', 'Please check'])\n"
                f"    po.take_screenshot({page_key!r} + '_p0_mismatch_toast', full_page=True)\n"
                f"    logger.end(success=True)\n"
            )

        happy_path_block = ""
        if happy_sel:
            happy_path_block = (
                f"\n\n@pytest.mark.P0\n"
                f"@pytest.mark.functional\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P0')\n"
                f"@allure.title('主流程：修改并保存（带回滚）')\n"
                f"def test_p0_happy_path_update_save_with_rollback(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    selector = {happy_sel!r}\n"
                f"    if page.locator(selector).count() == 0:\n"
                f"        pytest.skip('字段不可见/不存在（页面结构变化或 selector 失效）')\n\n"
                f"    snap = snapshot_inputs(page, FIELD_RULES)\n"
                f"    original = page.input_value(selector)\n"
                f"    new_value = (original or 'QA') + 'X'\n\n"
                f"    try:\n"
                f"        with allure.step('修改字段并保存'):\n"
                f"            page.fill(selector, new_value)\n"
                f"            po.take_screenshot({page_key!r} + '_p0_before_save')\n"
                f"            click_save(page)\n"
                f"            resp = wait_mutation_response(page, timeout_ms=60000)\n"
                f"            assert_not_redirected_to_login(page)\n"
                f"            if resp is not None:\n"
                f"                assert resp.status < 500, f'unexpected api status: {{resp.status}}'\n"
                f"            assert not has_any_error_ui(page), 'unexpected error UI after save'\n"
                f"            po.take_screenshot({page_key!r} + '_p0_after_save')\n"
                f"    finally:\n"
                f"        with allure.step('回滚（UI 级恢复）'):\n"
                f"            restore_inputs(page, snap)\n"
                f"            click_save(page)\n"
                f"            _ = wait_mutation_response(page, timeout_ms=60000)\n"
                f"            po.take_screenshot({page_key!r} + '_p0_after_rollback')\n\n"
                f"    logger.end(success=True)\n"
            )

        body = f"""@pytest.mark.P0
@pytest.mark.functional
@allure.feature({class_name!r})
@allure.story("P0")
@allure.title("页面加载")
def test_p0_page_load(auth_page: Page):
    logger.start()
    page = auth_page
    po = {class_name}Page(page)

    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "page not loaded"
    po.take_screenshot({page_key!r} + "_p0_page_load", full_page=True)
    logger.end(success=True)

{change_password_p0}
{happy_path_block}
{required_block}
"""
        return self._render_test_module(
            title=f"{class_name} - P0",
            playwright_import="from playwright.sync_api import Page",
            file_name=file_name,
            class_name=class_name,
            helper_mod=helper_mod,
            helper_symbols=[
                "FIELD_RULES",
                "assert_not_redirected_to_login",
                "assert_any_validation_evidence",
                "assert_toast_contains_any",
                "click_save",
                "has_any_error_ui",
                "snapshot_inputs",
                "restore_inputs",
                "wait_mutation_response",
            ],
            page_key=page_key,
            logger_suffix="_p0",
            body=body,
        )
