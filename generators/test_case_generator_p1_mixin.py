"""
TestCaseGenerator P1 template builder.
"""

from __future__ import annotations

from typing import Dict, List

from generators.page_types import PageInfo
from generators.utils import get_file_name_from_url, get_page_name_from_url, to_class_name, to_snake_case


class TestCaseGeneratorP1Mixin:
    def _p1_py(
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

        boundary_blocks: List[str] = []
        boundary_rules = [r for r in (rules or []) if isinstance(r.get("max_len"), int) and r.get("selector")]
        for r in boundary_rules:
            field = r.get("field") or "field"
            sel = r.get("selector")
            max_len = int(r.get("max_len"))
            html_type = (r.get("html_type") or "")
            src_comment = self._render_sources_comment(r)
            boundary_blocks.append(
                f"\n\n{src_comment}\n"
                f"@pytest.mark.P1\n"
                f"@pytest.mark.boundary\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P1')\n"
                f"@allure.title('边界值：{field} maxLength={max_len}')\n"
                f"def test_p1_{to_snake_case(field)}_length_boundary(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    selector = {sel!r}\n"
                f"    if page.locator(selector).count() == 0:\n"
                f"        pytest.skip('字段不可见/不存在（页面结构变化或 selector 失效）')\n\n"
                f"    original = page.input_value(selector)\n\n"
                f"    for n in [{max_len - 1}, {max_len}, {max_len + 1}]:\n"
                f"        if n <= 0:\n"
                f"            continue\n"
                f"        with allure.step(f'fill len={{n}}'):\n"
                f"            if {html_type!r} == 'email' or {field.lower()!r} in ['email', 'e-mail']:\n"
                f"                local_len = max(1, n - len('@t.com'))\n"
                f"                value = ('a' * local_len) + '@t.com'\n"
                f"                page.fill(selector, value)\n"
                f"            else:\n"
                f"                page.fill(selector, 'A' * n)\n\n"
                f"            click_save(page)\n"
                f"            resp = wait_mutation_response(page, timeout_ms=60000 if n <= {max_len} else 1500)\n"
                f"            assert_not_redirected_to_login(page)\n"
                f"            if resp is not None:\n"
                f"                assert resp.status < 500, f'unexpected api status: {{resp.status}}'\n\n"
                f"    page.fill(selector, original)\n"
                f"    click_save(page)\n"
                f"    _ = wait_mutation_response(page, timeout_ms=60000)\n\n"
                f"    po.take_screenshot('{page_key}_p1_{to_snake_case(field)}_length_boundary')\n"
                f"    logger.end(success=True)\n"
            )

        email_rule = next(
            (
                r
                for r in (rules or [])
                if r.get("selector")
                and ((r.get("html_type") == "email") or ((r.get("field") or "").lower() in {"email", "e-mail"}))
            ),
            None,
        )
        if email_rule is None:
            email_block = ""
        else:
            field = email_rule.get("field") or "email"
            sel = email_rule.get("selector")
            src_comment = self._render_sources_comment(email_rule)
            email_block = (
                f"\n\n{src_comment}\n"
                f"@pytest.mark.P1\n"
                f"@pytest.mark.validation\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P1')\n"
                f"@allure.title('格式校验：Email 非法格式（HTML5 validity）')\n"
                f"def test_p1_email_invalid_format_should_fail(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    selector = {sel!r}\n"
                f"    if page.locator(selector).count() == 0:\n"
                f"        pytest.skip('Email 字段不可见/不存在（页面结构变化或 selector 失效）')\n\n"
                f"    original = page.input_value(selector)\n"
                f"    page.fill(selector, 'not-an-email')\n"
                f"    click_save(page)\n\n"
                f"    is_valid = page.eval_on_selector(selector, 'el => el.checkValidity()')\n"
                f"    assert is_valid is False, 'expected HTML5 email validity to reject invalid email'\n\n"
                f"    resp = wait_mutation_response(page, timeout_ms=1500)\n"
                f"    assert resp is None, 'expected no mutation request when email is invalid'\n"
                f"    po.take_screenshot('{page_key}_p1_email_invalid')\n\n"
                f"    page.fill(selector, original)\n"
                f"    click_save(page)\n"
                f"    _ = wait_mutation_response(page, timeout_ms=60000)\n\n"
                f"    logger.end(success=True)\n"
            )

        api_failure_block = ""
        if is_change_password:
            api_failure_block = (
                f"\n\n@pytest.mark.P1\n"
                f"@pytest.mark.exception\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P1')\n"
                f"@allure.title('API 错误处理：旧密码错误应返回 4xx 且给出错误提示')\n"
                f"def test_p1_api_failure_on_save(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    po.fill_currentpassword('wrong-current-123')\n"
                f"    po.fill_newpassword('NewPass_123')\n"
                f"    po.fill_confirmnewpassword('NewPass_123')\n"
                f"    click_save(page)\n"
                f"    resp = wait_response_by_url_substring(page, CHANGE_PASSWORD_API_PATH, method='POST', timeout_ms=60000)\n"
                f"    assert_not_redirected_to_login(page)\n"
                f"    assert 400 <= resp.status < 500, f'expected 4xx, got {{resp.status}}'\n"
                f"    assert_toast_contains_any(page, ['Incorrect password', 'Failed', '密码'])\n"
                f"    po.take_screenshot('{page_key}_p1_wrong_current_toast', full_page=True)\n"
                f"    logger.end(success=True)\n"
            )
        else:
            api_failure_block = (
                f"\n\n@pytest.mark.P1\n"
                f"@pytest.mark.exception\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P1')\n"
                f"@allure.title('API 错误处理：写请求被拦截（兜底）')\n"
                f"def test_p1_api_failure_on_save(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    aborted = {{'value': False}}\n\n"
                f"    def abort_mutation(route):\n"
                f"        if route.request.method in {{'PUT', 'POST', 'PATCH'}}:\n"
                f"            aborted['value'] = True\n"
                f"            route.abort()\n"
                f"        else:\n"
                f"            route.continue_()\n\n"
                f"    page.route('**/*', abort_mutation)\n"
                f"    try:\n"
                f"        click_save(page)\n"
                f"        _ = wait_mutation_response(page, timeout_ms=3000)\n"
                f"        assert_not_redirected_to_login(page)\n"
                f"        assert aborted['value'] is True, 'expected a write request to be aborted'\n"
                f"        # 这里不强行断言 UI，因为不同产品对 network error 的反馈差异很大。\n"
                f"        po.take_screenshot('{page_key}_p1_api_failure')\n"
                f"    finally:\n"
                f"        page.unroute('**/*', abort_mutation)\n\n"
                f"    logger.end(success=True)\n"
            )

        mismatch_block = ""
        if is_change_password:
            mismatch_block = (
                f"\n\n@pytest.mark.P1\n"
                f"@pytest.mark.validation\n"
                f"@allure.feature({class_name!r})\n"
                f"@allure.story('P1')\n"
                f"@allure.title('一致性校验：新密码不一致时不应触发后端写请求')\n"
                f"def test_p1_mismatch_should_not_call_change_password_api(auth_page: Page):\n"
                f"    logger.start()\n"
                f"    page = auth_page\n"
                f"    po = {class_name}Page(page)\n\n"
                f"    po.navigate()\n"
                f"    assert_not_redirected_to_login(page)\n\n"
                f"    called = {{'value': False}}\n\n"
                f"    def observe(route):\n"
                f"        if route.request.method == 'POST' and (CHANGE_PASSWORD_API_PATH in (route.request.url or '')):\n"
                f"            called['value'] = True\n"
                f"        route.continue_()\n\n"
                f"    page.route('**/*', observe)\n"
                f"    try:\n"
                f"        po.fill_currentpassword('wrong-current-123')\n"
                f"        po.fill_newpassword('NewPass_123')\n"
                f"        po.fill_confirmnewpassword('NewPass_124')\n"
                f"        click_save(page)\n"
                f"        assert_not_redirected_to_login(page)\n"
                f"        assert_toast_contains_any(page, ['Confirm', '确认', 'Please check'])\n"
                f"        assert called['value'] is False, 'mismatch should be blocked on frontend before calling API'\n"
                f"        po.take_screenshot('{page_key}_p1_mismatch_no_api', full_page=True)\n"
                f"    finally:\n"
                f"        page.unroute('**/*', observe)\n\n"
                f"    logger.end(success=True)\n"
            )

        boundary_block = "".join(boundary_blocks)

        body = f"""{boundary_block}
{email_block}
{mismatch_block}
{api_failure_block}
"""
        return self._render_test_module(
            title=f"{class_name} - P1",
            playwright_import="from playwright.sync_api import Page",
            file_name=file_name,
            class_name=class_name,
            helper_mod=helper_mod,
            helper_symbols=[
                "FIELD_RULES",
                "CHANGE_PASSWORD_API_PATH",
                "assert_not_redirected_to_login",
                "assert_toast_contains_any",
                "click_save",
                "has_any_error_ui",
                "wait_response_by_url_substring",
                "wait_mutation_response",
            ],
            page_key=page_key,
            logger_suffix="_p1",
            body=body,
        )
