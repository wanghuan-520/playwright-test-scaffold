"""
Account/Register - ABP 约束测试辅助（仅供测试代码使用）

职责：
- 聚合 “max+1 前端截断” 与 “必填/最小值” 的证据驱动断言与构造器
- 让 test 文件保持短小（< 400 行），并减少重复实现
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from tests.Account.Register._helpers import (
    detect_fatal_error_page,
    has_any_error_ui,
    wait_mutation_response,
    wait_response_by_url_substring,
)

__all__ = [
    "ABP_MAX_LEN_COMMON",
    "ABP_PASSWORD_MAX",
    "ABP_PASSWORD_MIN",
    "DESC_MAXLENGTH_EVIDENCE",
    "DESC_REQUIRED_ATTR_EVIDENCE",
    "DESC_REQUIRED_EMPTY_KNOWN_BUG",
    "DESC_PASSWORD_MIN_EVIDENCE",
    "DESC_USERNAME_BOUNDARY",
    "DESC_EMAIL_BOUNDARY",
    "DESC_PASSWORD_BOUNDARY",
    "has_any_error_ui",
    "get_attr",
    "get_maxlength_attr",
    "mk_username_with_len",
    "mk_email_with_len",
    "mk_email_len_max_plus_one",
    "read_input_len",
    "assert_frontend_truncated",
    "ensure_register_page",
    "fill_baseline",
    "set_field",
    "try_get_submit_response",
    "attach_register_payload_lens",
    "assert_no_fatal_error",
    "assert_validation_evidence",
]

# -----------------------------------------------------------------------------
# 常量（与 ABP/AuthServer 常见约束对齐）
# -----------------------------------------------------------------------------
ABP_MAX_LEN_COMMON = 256
ABP_PASSWORD_MAX = 128
ABP_PASSWORD_MIN = 6

# -----------------------------------------------------------------------------
# Allure Description（尽量“内容清楚”，但“物理行数少”）
# -----------------------------------------------------------------------------
DESC_MAXLENGTH_EVIDENCE = (
    "目的：给“max+1 前端截断/阻止输入”提供可审计证据（仅输入层取证）。\n"
    "输入：Username='x'*(256+10), Email=('a'*(256+5))+'@t.com', Password='x'*(128+10)。\n"
    "观测：读取 maxlength 属性（若有）+ input_value 实际长度。\n"
    "判据：actual_len 必须 ≤ max（256/128），即超长部分在前端被截断/阻止；不点击 Register，不依赖后端。"
)
DESC_REQUIRED_ATTR_EVIDENCE = (
    "目的：确认 Register 页是否在前端标注“必填”（可观测证据）。\n"
    "观测：required / aria-required / data-val-required（任一存在即可视为“可观测必填标注”）。\n"
    "说明：若三者都缺失，则用例 xfail（表示“前端缺少可观测标注”，不等价于后端不校验）。"
)
DESC_REQUIRED_EMPTY_KNOWN_BUG = (
    "已知缺陷用例（xfail）：必填字段置空提交不应触发 500/错误页。\n"
    "Baseline：Username=qatest_baseline, Email=qatest_baseline@testmail.com, Password=ValidPass123!；随后清空一个字段提交。\n"
    "判据：不得进入致命错误页（当前产品缺陷会触发，因此 xfail）。"
)
DESC_PASSWORD_MIN_EVIDENCE = (
    "目的：验证 Password 最小长度（min=6）在提交时能产生“可观测校验证据”。\n"
    "输入：Password='Aa1!a'（len=5，满足大小写/数字/特殊字符，仅违反 min length）。\n"
    "判据：出现任一校验证据（error UI 或后端 4xx）；不得进入致命错误页。"
)
DESC_USERNAME_BOUNDARY = (
    "边界值三点采样：max-1/max/max+1（255/256/257）。\n"
    "Baseline：Username=qatest_{uuid}, Email=qatest_{uuid}@testmail.com, Password=ValidPass123!。\n"
    "目标输入：suffix=uuid[:10]；typed_username(total_len)=('u'*(total_len-len(suffix)))+suffix。\n"
    "期望：255/256 允许提交（无 error UI；若抓到响应则非 4xx/5xx）；257 必须前端截断，且 input_value==typed[:256]，截断后等价 256 同判据。"
)
DESC_EMAIL_BOUNDARY = (
    "边界值三点采样：max-1/max/max+1（255/256/257）。\n"
    "Baseline：Username=qatest_{uuid}, Email=qatest_{uuid}@testmail.com, Password=ValidPass123!。\n"
    "目标输入：suffix=uuid[:10]；255/256 用 '@t.com'；257 用 '@t.comm'（截断 1 字符后变 '@t.com'，仍是合法 email）。\n"
    "期望：255/256 允许提交（无 error UI；若抓到响应则非 4xx/5xx）；257 必须前端截断，且 input_value==typed_257[:256]，截断后等价 256 同判据。"
)
DESC_PASSWORD_BOUNDARY = (
    "边界值三点采样：max-1/max/max+1（127/128/129），仅验证“长度边界/截断”，复杂密码策略在 password_policy_matrix 覆盖。\n"
    "Baseline：Username=qatest_{uuid}, Email=qatest_{uuid}@testmail.com, Password=ValidPass123!。\n"
    "目标输入：typed_password(total_len)=('A'*(total_len-4))+'a1!a'（确保包含 a1!a）。\n"
    "期望：127/128 允许提交（无 error UI；若抓到响应则非 4xx/5xx）；129 必须前端截断，且 input_value==typed[:128]，截断后等价 128 同判据。"
)


# -----------------------------------------------------------------------------
# DOM/输入构造
# -----------------------------------------------------------------------------
def get_attr(page: Page, selector: str, attr: str) -> str:
    if not selector or not attr:
        return ""
    try:
        if page.locator(selector).count() == 0:
            return ""
    except Exception:
        return ""
    try:
        return (page.eval_on_selector(selector, f"el => el.getAttribute('{attr}')") or "").strip()
    except Exception:
        return ""


def get_maxlength_attr(page: Page, selector: str) -> str:
    return get_attr(page, selector, "maxlength")


def mk_username_with_len(total_len: int, suffix: str) -> str:
    suffix = (suffix or "")
    if total_len <= 0:
        return ""
    suffix = suffix[: min(len(suffix), total_len)]
    return ("u" * max(total_len - len(suffix), 0)) + suffix


def mk_email_with_len(total_len: int, suffix: str) -> str:
    domain = "@t.com"  # len=5
    if total_len <= len(domain):
        return f"a{domain}"
    local_len = total_len - len(domain)
    suffix = (suffix or "")[: min(len(suffix or ""), local_len)]
    local = ("a" * max(local_len - len(suffix), 0)) + suffix
    return f"{local}{domain}"


def mk_email_len_max_plus_one(suffix: str) -> str:
    # 用 @t.comm（len=6），截断 1 字符后变 @t.com（len=5），仍合法
    domain = "@t.comm"
    total_len = ABP_MAX_LEN_COMMON + 1
    local_len = total_len - len(domain)
    s = (suffix or "")[: max(local_len, 0)]
    local = ("a" * max(local_len - len(s), 0)) + s
    return f"{local}{domain}"


def read_input_len(page: Page, selector: str) -> int:
    try:
        return len(page.input_value(selector) or "")
    except Exception:
        return -1


def assert_frontend_truncated(page: Page, selector: str, typed_value: str, *, expected_max: int, case_name: str) -> None:
    maxlength_attr = get_maxlength_attr(page, selector)
    try:
        actual = page.input_value(selector) or ""
    except Exception:
        actual = ""
    want = (typed_value or "")[:expected_max]
    allure.attach(
        f"case={case_name}\nselector={selector}\nmaxlength_attr={maxlength_attr!r}\n"
        f"typed_len={len(typed_value or '')}\nactual_len={len(actual)}\nexpected_max={expected_max}\n"
        f"expected_tail={want[-12:]!r}\nactual_tail={actual[-12:]!r}\n",
        name=f"{case_name}_truncate_evidence",
        attachment_type=allure.attachment_type.TEXT,
    )
    assert actual == want, f"{case_name}: expected truncate exactly to typed[:{expected_max}] (maxlength={maxlength_attr!r})"


def ensure_register_page(page: Page, po) -> None:
    try:
        if page.locator(po.USERNAME_INPUT).count() > 0:
            return
    except Exception:
        pass
    po.navigate()
    page.wait_for_timeout(200)


def fill_baseline(po, *, suffix: str) -> None:
    po.fill_username(f"qatest_{suffix}")
    po.fill_email_address(f"qatest_{suffix}@testmail.com")
    po.fill_password("ValidPass123!")


def set_field(po, field: str, value: str) -> None:
    if field == "username":
        po.fill_username(value)
        return
    if field == "email":
        po.fill_email_address(value)
        return
    if field == "password":
        po.fill_password(value)
        return
    raise AssertionError(f"unknown field: {field}")


# -----------------------------------------------------------------------------
# 提交/证据断言（best-effort response）
# -----------------------------------------------------------------------------
def try_get_submit_response(page: Page, *, timeout_ms: int):
    try:
        return wait_response_by_url_substring(page, "/api/account/register", timeout_ms=timeout_ms)
    except Exception:
        return wait_mutation_response(page, timeout_ms=timeout_ms)


def attach_register_payload_lens(resp, *, name: str) -> None:
    if resp is None:
        return
    try:
        req = resp.request
        payload = {}
        try:
            payload = req.post_data_json or {}
        except Exception:
            payload = {}
        uname = str(payload.get("userName") or "")
        email = str(payload.get("emailAddress") or "")
        pwd = str(payload.get("password") or "")
        allure.attach(
            f"request_payload_lens: userName={len(uname)} emailAddress={len(email)} password={len(pwd)}\nresponse_status={resp.status}",
            name=name,
            attachment_type=allure.attachment_type.TEXT,
        )
    except Exception:
        return


def assert_no_fatal_error(page: Page, *, case_name: str) -> None:
    fatal = detect_fatal_error_page(page)
    if fatal:
        allure.attach(fatal, name=f"{case_name}_fatal_error_page", attachment_type=allure.attachment_type.TEXT)
        raise AssertionError(f"[{case_name}] fatal error page detected: {fatal}")


def assert_validation_evidence(page: Page, selector: str, *, case_name: str) -> None:
    # 证据优先级：error UI > 4xx（避免依赖 validationMessage 的浏览器文案）
    if has_any_error_ui(page):
        return
    resp = wait_mutation_response(page, timeout_ms=3000)
    if resp is not None:
        assert resp.status < 500, f"{case_name}: unexpected 5xx status={resp.status}"
        if 400 <= resp.status < 500:
            return
    allure.attach(
        f"no observable evidence (no error UI / no 4xx). case={case_name}",
        name=f"{case_name}_no_observable_evidence",
        attachment_type=allure.attachment_type.TEXT,
    )
    raise AssertionError(f"[{case_name}] no observable validation evidence")


