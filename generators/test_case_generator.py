# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Case Generator
# ═══════════════════════════════════════════════════════════════
"""测试用例生成器

强制目标（与项目规则对齐）：
- 用户说“测试某页面/URL”默认生成完整套件：P0/P1/P2/security。
- **首次生成就必须参照前后端代码推导字段规则**；若配置了本地 repo 路径但推导失败，拒绝“凭猜”。
- 生成的测试用例采用**函数式**（不生成 Test* class），压扁 Allure suites 树的 class 层级。

注意：这里的“规则推导”是可演进的最小实现：
- 优先解析前端 react-hook-form register()；
- 后端 DTO attributes 轻量补充；
- DOM 动态信息只用于 selector/type 兜底，不当作规则真理。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import pprint

from generators.page_types import PageInfo
from generators.rule_deriver import RuleDeriver
from generators.utils import extract_url_path, get_file_name_from_url, get_page_name_from_url, to_class_name, to_snake_case
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerator:
    """生成测试用例（多文件套件）。"""

    def generate_test_suite(self, page_info: PageInfo) -> Optional[Dict[str, str]]:
        # 可执行规则：决定套件包含哪些文件（p0/p1/p2/security）
        enabled = {"p0", "p1", "p2", "security"}
        try:
            from utils.rules_engine import get_rules_config

            cfg = get_rules_config()
            enabled = {str(x).strip().lower() for x in (cfg.suite_files or ()) if str(x).strip()}
            enabled = enabled & {"p0", "p1", "p2", "security"} if enabled else {"p0", "p1", "p2", "security"}
        except Exception:
            pass

        url_path = extract_url_path(page_info.url)
        segments = [s for s in url_path.strip("/").split("/") if s]
        module, page = self._infer_module_and_page(segments)
        base_dir = f"tests/{module}/{page}"

        page_key = self._infer_page_key(page, page_info.page_type)
        is_change_password = self._is_change_password_page(url_path=url_path, page_info=page_info)

        # 规则推导（强制：有本地 repo 路径就必须推导；否则拒绝凭猜）
        cfg = ConfigManager()
        deriver = RuleDeriver.from_config(cfg)
        rules = deriver.derive(page_info)

        has_static_repo = bool(cfg.get("repositories.frontend.local_path", "")) or bool(cfg.get("repositories.backend.local_path", ""))
        if has_static_repo and not rules:
            raise RuntimeError(
                "Static rule derivation failed (repositories.*.local_path provided but no rules derived). "
                "Refusing to guess. Please fix repo path or parsing logic."
            )

        suite: Dict[str, str] = {
            f"tests/{module}/__init__.py": "",
            f"{base_dir}/__init__.py": "",
            f"{base_dir}/_helpers.py": self._helpers_py(page_info, rules, is_change_password=is_change_password),
        }
        if "p0" in enabled:
            suite[f"{base_dir}/test_{page_key}_p0.py"] = self._p0_py(
                page_info, module, page, page_key, rules, is_change_password=is_change_password
            )
        if "p1" in enabled:
            suite[f"{base_dir}/test_{page_key}_p1.py"] = self._p1_py(
                page_info, module, page, page_key, rules, is_change_password=is_change_password
            )
        if "p2" in enabled:
            suite[f"{base_dir}/test_{page_key}_p2.py"] = self._p2_py(page_info, module, page, page_key, rules)
        if "security" in enabled:
            suite[f"{base_dir}/test_{page_key}_security.py"] = self._security_py(page_info, module, page, page_key, rules)

        return suite

    # Backward-compatible fallback
    def generate_test_cases(self, page_info: PageInfo) -> str:
        suite = self.generate_test_suite(page_info)
        if not suite:
            raise RuntimeError("suite generation disabled")
        # 返回一个可读提示，不再生成旧的单文件 class 结构
        return (
            "# This project generates a multi-file test suite by default.\n"
            "# Use TestCodeGenerator.generate_all(page_info) to write files to disk.\n"
        )

    # ═══════════════════════════════════════════════════════════════
    # Naming
    # ═══════════════════════════════════════════════════════════════

    def _infer_module_and_page(self, segments: List[str]) -> Tuple[str, str]:
        if not segments:
            return "root", "home"
        if len(segments) == 1:
            return segments[0], segments[0]
        # 规则：
        # - 默认：tests/<module>/<page>（取前两段）
        # - 但当 URL 更深（>=3 段）时，如果仍只取前两段，会把“子页面”覆盖到同一个目录，
        #   例如：/admin/profile 与 /admin/profile/change-password 都会落到 tests/admin/profile。
        #   这会导致生成器覆盖已有套件（灾难）。
        #
        # 解决：把第 2 段之后的 path 也纳入 page 名（用 '_' 连接，并做包名安全化）。
        module = segments[0]
        page_parts = segments[1:]
        # package name sanitize: '-' -> '_'（保留其它字符交给后续工具/py 解析的最小假设）
        safe_parts = [(p or "").replace("-", "_") for p in page_parts if p]
        page = "_".join(safe_parts) if safe_parts else segments[1]
        return module, page

    def _infer_page_key(self, page: str, page_type: str) -> str:
        return f"{page}_settings" if page_type == "SETTINGS" else page

    def _is_change_password_page(self, *, url_path: str, page_info: PageInfo) -> bool:
        """
        针对“修改密码”页的专项模板：
        - 该页面通常只有 password 字段，没有可安全回滚的“普通字段”，happy path 不应凭猜生成。
        - 用例应围绕：必填、两次输入一致性、后端 4xx 错误处理、安全输入。
        """
        p = (url_path or "").lower()
        if "change-password" in p or "change_password" in p:
            return True
        name = (get_page_name_from_url(page_info.url) or "").lower()
        return "changepassword" in name or "change_password" in name

    # ═══════════════════════════════════════════════════════════════
    # Suite files
    # ═══════════════════════════════════════════════════════════════

    def _helpers_py(self, page_info: PageInfo, rules: List[Dict], *, is_change_password: bool) -> str:
        url_path = extract_url_path(page_info.url)
        rules_literal = self._py_literal(rules)
        change_password_api = "/api/account/my-profile/change-password"
        # 让常量“永远存在”：避免生成的测试文件需要做条件 import。
        # 非 change-password 页面时设为空字符串即可（相关专项用例也不会生成）。
        change_password_api_line = (
            f"CHANGE_PASSWORD_API_PATH = {change_password_api!r}\n" if is_change_password else "CHANGE_PASSWORD_API_PATH = ''\n"
        )
        return f"""# ═══════════════════════════════════════════════════════════════
# Helpers
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════
# 通用小工具：让用例更短、更稳。

from __future__ import annotations

from typing import Dict, Optional

from playwright.sync_api import Page, Response, expect


URL_PATH = {url_path!r}
{change_password_api_line}

# 字段规则（由前后端代码推导；若来源缺失则会降级/skip）
FIELD_RULES = {rules_literal}

ERROR_SELECTORS = [
    ".invalid-feedback",
    ".text-danger",
    ".error-message",
    ".field-error",
    ".toast-error",
    ".Toastify__toast--error",
    "p.text-red-500",
]


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {{url}}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {{url}}"


def click_save(page: Page) -> None:
    # 尽量用文案锁定，避免命中同 class 的非目标按钮
    btn = page.locator("button:has-text('Save')").first
    expect(btn).to_be_visible()
    expect(btn).to_be_enabled()
    btn.click()


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    # 等待任意写操作响应（PUT/POST/PATCH）。存在则返回，否则返回 None。
    try:
        with page.expect_response(lambda r: (r.request.method in ("PUT", "POST", "PATCH")), timeout=timeout_ms) as resp_info:
            pass
        return resp_info.value
    except Exception:
        return None


def wait_response_by_url_substring(page: Page, url_substring: str, *, method: str = "POST", timeout_ms: int = 60000) -> Response:
    with page.expect_response(
        lambda r: (r.request.method == method) and (url_substring in (r.url or "")),
        timeout=timeout_ms,
    ) as resp_info:
        pass
    return resp_info.value


def get_validation_message(page: Page, selector: str) -> str:
    \"\"\"读取浏览器原生表单校验文案（required/pattern 等）。\"\"\"
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage")
        return (msg or "").strip()
    except Exception:
        return ""


def assert_any_validation_evidence(page: Page, selector: str) -> None:
    \"\"\"
    必填/格式校验的“证据合取”：只要命中任意一种即可。
    - 原生 validationMessage（最稳定）
    - 页面错误 UI（toast/field error）
    - 后端 4xx（实现把 required 放到后端也算通过）
    \"\"\"
    msg = get_validation_message(page, selector)
    if msg:
        return
    if has_any_error_ui(page):
        return
    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None and (400 <= resp.status < 500):
        return
    raise AssertionError("no validation evidence observed (validationMessage/error UI/4xx)")


def wait_for_toast(page: Page, timeout_ms: int = 3000) -> None:
    \"\"\"等待通知区域出现至少一条 toast。\"\"\"
    regions = page.get_by_role("region", name="Notifications (F8)")
    picked = None
    try:
        n = regions.count()
    except Exception:
        n = 0
    for i in range(max(n, 1)):
        r = regions.nth(i) if n > 0 else regions
        try:
            if r.is_visible(timeout=200):
                picked = r
                break
        except Exception:
            continue
    region = picked or regions.first
    item = region.get_by_role("listitem").first
    expect(item).to_be_visible(timeout=timeout_ms)


def get_toast_text(page: Page) -> str:
    regions = page.get_by_role("region", name="Notifications (F8)")
    try:
        n = regions.count()
    except Exception:
        n = 0
    if n == 0:
        return ""
    for i in range(n):
        r = regions.nth(i)
        try:
            if not r.is_visible(timeout=200):
                continue
            return (r.inner_text(timeout=1000) or "").strip()
        except Exception:
            continue
    try:
        return (regions.first.inner_text(timeout=1000) or "").strip()
    except Exception:
        return ""


def assert_toast_contains_any(page: Page, needles: list[str]) -> None:
    wait_for_toast(page, timeout_ms=3000)
    text = get_toast_text(page)
    assert any((n or "") in text for n in (needles or [])), f"toast text not matched. want any={{needles}} got={{text!r}}"


def has_any_error_ui(page: Page) -> bool:
    for sel in ERROR_SELECTORS:
        try:
            if page.is_visible(sel, timeout=500):
                return True
        except Exception:
            continue
    return False


def snapshot_inputs(page: Page, rules: list[dict]) -> Dict[str, str]:
    # 按规则列表对输入框做 UI 快照（selector -> value）。
    snap: Dict[str, str] = dict()
    for r in rules:
        sel = r.get("selector") or ""
        if not sel:
            continue
        if page.locator(sel).count() == 0:
            continue
        try:
            snap[sel] = page.input_value(sel)
        except Exception:
            continue
    return snap


def restore_inputs(page: Page, snap: Dict[str, str]) -> None:
    # UI 级恢复（不依赖后端特定 API）。
    for sel, val in snap.items():
        try:
            if page.locator(sel).count() == 0:
                continue
            page.fill(sel, val)
        except Exception:
            continue
"""

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
        # P0 happy path：避免对 password 字段做“随意改一位然后保存”的主流程（通常会触发后端校验失败）。
        # 选择“非 password”的可写字段作为最小主链路载体；若不存在则让 happy path 自动 skip。
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

        # change-password 专项：生成稳定 P0（不依赖真实旧密码）
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

        return f"""# ═══════════════════════════════════════════════════════════════
# {class_name} - P0
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.{file_name}_page import {class_name}Page
from {helper_mod} import (
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

logger = TestLogger({page_key!r} + "_p0")


@pytest.mark.P0
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
        # 不再生成“自动跳过”的占位用例：没推导出规则就不生成该类 P1。
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

        # change-password 专项：用确定性 4xx + toast 覆盖“错误处理”，不再用 route abort 这种不稳定兜底。
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

        return f"""# ═══════════════════════════════════════════════════════════════
# {class_name} - P1
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page

from pages.{file_name}_page import {class_name}Page
from {helper_mod} import (
    FIELD_RULES,
    CHANGE_PASSWORD_API_PATH,
    assert_not_redirected_to_login,
    assert_toast_contains_any,
    click_save,
    has_any_error_ui,
    wait_response_by_url_substring,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger({page_key!r} + "_p1")

{boundary_block}
{email_block}
{mismatch_block}
{api_failure_block}
"""

    def _p2_py(self, page_info: PageInfo, module: str, page: str, page_key: str, rules: List[Dict]) -> str:
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        file_name = get_file_name_from_url(page_info.url)
        helper_mod = f"tests.{module}.{page}._helpers"

        selectors = [r.get("selector") for r in (rules or []) if r.get("selector")]
        selectors_literal = self._py_literal([s for s in selectors if isinstance(s, str)])

        return f"""# ═══════════════════════════════════════════════════════════════
# {class_name} - P2
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.{file_name}_page import {class_name}Page
from {helper_mod} import assert_not_redirected_to_login
from utils.logger import TestLogger

logger = TestLogger({page_key!r} + "_p2")


@pytest.mark.P2
@pytest.mark.ui
@allure.feature({class_name!r})
@allure.story("P2")
@allure.title("UI：字段可见性 + 全页截图")
def test_p2_fields_visible(auth_page: Page):
    logger.start()
    page = auth_page
    po = {class_name}Page(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出字段 selector（P2 可见性用例跳过）")

    for selector in selectors:
        expect(page.locator(selector)).to_be_visible()

    po.take_screenshot({page_key!r} + "_p2_fields_visible", full_page=True)
    logger.end(success=True)


@pytest.mark.P2
@pytest.mark.ui
@allure.feature({class_name!r})
@allure.story("P2")
@allure.title("UI：键盘 Tab 可用性")
def test_p2_keyboard_tab_navigation(auth_page: Page):
    logger.start()
    page = auth_page
    po = {class_name}Page(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出字段 selector（Tab 用例跳过）")

    page.click(selectors[0])
    for _ in range(min(5, len(selectors))):
        page.keyboard.press("Tab")

    po.take_screenshot({page_key!r} + "_p2_keyboard_tab")
    logger.end(success=True)
"""

    def _security_py(self, page_info: PageInfo, module: str, page: str, page_key: str, rules: List[Dict]) -> str:
        class_name = to_class_name(get_page_name_from_url(page_info.url))
        url_path = extract_url_path(page_info.url)
        helper_mod = f"tests.{module}.{page}._helpers"
        is_protected = "/admin/" in url_path

        # selectors for injection
        selectors = [r.get("selector") for r in (rules or []) if r.get("selector")]
        selectors_literal = self._py_literal([s for s in selectors if isinstance(s, str)])

        return f"""# ═══════════════════════════════════════════════════════════════
# {class_name} - Security
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
import re
from playwright.sync_api import Page

from utils.config import ConfigManager
from {helper_mod} import (
    URL_PATH,
    assert_not_redirected_to_login,
    click_save,
    snapshot_inputs,
    restore_inputs,
    wait_mutation_response,
)
from utils.logger import TestLogger

logger = TestLogger({page_key!r} + "_security")


@pytest.mark.P1
@pytest.mark.security
@allure.feature({class_name!r})
@allure.story("Security")
@allure.title("未登录访问受保护页面应跳转登录")
def test_security_unauth_redirects_to_login(unauth_page: Page):
    logger.start()

    if {str(is_protected)} is False:
        pytest.skip("页面不在 /admin/ 路由下，默认不强制要求鉴权跳转")

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{{base}}{{URL_PATH}}"

    page = unauth_page
    # 只要“发生导航并提交”即可，login 页是否完成 domcontentloaded 不应影响鉴权跳转判断
    page.goto(url, wait_until="commit", timeout=60000)
    page.wait_for_url(re.compile(r".*(/auth/login|/Account/Login).*"), timeout=60000)

    current = page.url or ""
    assert "/auth/login" in current or "/Account/Login" in current, f"expected redirect to login, got: {{current}}"
    page.screenshot(path=f"screenshots/{page_key}_security_unauth_redirect.png", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.security
@allure.feature({class_name!r})
@allure.story("Security")
@allure.title("XSS/SQLi payload 不得触发 dialog")
def test_security_xss_payload_no_dialog(auth_page: Page):
    logger.start()

    page = auth_page

    dialog_triggered = {{"value": False}}

    def on_dialog(_):
        dialog_triggered["value"] = True

    page.on("dialog", on_dialog)

    page.goto("https://localhost:3000" + URL_PATH, wait_until="domcontentloaded", timeout=60000)
    assert_not_redirected_to_login(page)

    selectors = {selectors_literal}
    if not selectors:
        pytest.skip("未推导出可注入的输入框 selector（拒绝凭猜）")

    snap = snapshot_inputs(page, [{{"selector": s}} for s in selectors])
    try:
        payloads = [
            "<img src=x onerror=alert(1)>",
            "' OR 1=1 --",
            "<script>alert(1)</script>",
        ]

        for sel in selectors:
            if page.locator(sel).count() == 0:
                continue
            for payload in payloads:
                page.fill(sel, payload)
                click_save(page)
                resp = wait_mutation_response(page, timeout_ms=1500)
                if resp is not None:
                    assert resp.status < 500, f"unexpected status after payload save: {{resp.status}}"
                assert_not_redirected_to_login(page)
                page.wait_for_timeout(200)
    finally:
        # 安全用例只验证“不执行/不崩溃”，不做保存回滚（避免 required 阻塞导致长等待）。
        # 恢复输入后直接 reload，让页面回到干净状态即可。
        restore_inputs(page, snap)
        try:
            page.reload()
        except Exception:
            pass
        page.wait_for_timeout(300)

    assert dialog_triggered["value"] is False, "XSS payload triggered a dialog"
    page.screenshot(path=f"screenshots/{page_key}_security_xss_no_dialog.png", full_page=True)

    logger.end(success=True)
"""

    # ═══════════════════════════════════════════════════════════════
    # String helpers
    # ═══════════════════════════════════════════════════════════════

    def _render_sources_comment(self, r: Dict) -> str:
        srcs = r.get("sources") or []
        if not srcs:
            return "# Source: (missing)"
        lines = []
        for s in srcs:
            kind = s.get("kind")
            path = s.get("path")
            detail = s.get("detail") or ""
            lines.append(f"# Source: {kind} {path} {detail}".rstrip())
        return "\n".join(lines)

    def _py_literal(self, obj) -> str:
        # Python literal（可直接 import），用于写入生成的 .py 文件
        # 注意：不能用 JSON（true/null 会导致 SyntaxError）。
        return pprint.pformat(obj, width=120, sort_dicts=False)
