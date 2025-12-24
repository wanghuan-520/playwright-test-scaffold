"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Diagnostics artifacts + per-test account allocation
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.fixture.shared import _collect_set_cookie_oversize, config, data_manager, logger


# ═══════════════════════════════════════════════════════════════
# TEST LOGGING
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def log_test_info(request):
    """自动记录测试信息"""
    test_name = request.node.name
    test_file = request.node.fspath.basename if hasattr(request.node, "fspath") else ""

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"▶️  开始测试: {test_file}::{test_name}")
    logger.info("=" * 60)

    yield

    logger.info(f"⏹️  结束测试: {test_name}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT / TRACE ON FAILURE
# ═══════════════════════════════════════════════════════════════

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试报告钩子 - 失败时自动截图"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function", autouse=True)
def artifacts_on_failure(request):
    """失败时自动收集诊断信息（截图/console/requestfailed/trace），并尽量附加到 Allure。"""
    console_lines = []
    requestfailed_lines = []
    set_cookie_oversize_lines = []

    def _get_page():
        wanted = set(getattr(request, "fixturenames", []) or [])
        for name in ("page", "test_page", "logged_in_page", "auth_page", "unauth_page"):
            if name not in wanted:
                continue
            try:
                return request.getfixturevalue(name)
            except Exception:
                continue
        return None

    page = _get_page()
    if page is not None:
        try:
            page.on("console", lambda m: console_lines.append(f"[{m.type}] {m.text}"))

            def _on_request_failed(req):
                try:
                    failure = req.failure
                    if isinstance(failure, dict):
                        failure = failure.get("errorText") or failure.get("error_text") or ""
                    elif failure is None:
                        failure = ""
                    else:
                        failure = str(failure)
                except Exception:
                    failure = ""
                requestfailed_lines.append(f"{req.method} {req.url} -> {failure}".strip())

            page.on("requestfailed", _on_request_failed)

            def _on_response(resp):
                try:
                    _collect_set_cookie_oversize(resp.headers, resp.url, resp.status, set_cookie_oversize_lines)
                except Exception:
                    pass

            page.on("response", _on_response)
        except Exception:
            pass

    yield

    failed = bool(getattr(request.node, "rep_call", None) and request.node.rep_call.failed)
    if not failed:
        return

    test_id = request.node.nodeid.replace("/", "_").replace("::", "_")

    try:
        import allure  # type: ignore
    except Exception:
        allure = None  # noqa: N816

    # 1) screenshot
    screenshot_path = Path("screenshots") / f"{test_id}_failure.png"
    if page is not None:
        try:
            screenshot_path.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"📸 失败截图已保存: {screenshot_path}")
            if allure is not None:
                allure.attach.file(
                    str(screenshot_path),
                    name="failure_screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
        except Exception as e:
            logger.error(f"截图失败: {e}")

    # 2) console logs
    if console_lines and allure is not None:
        try:
            allure.attach("\n".join(console_lines), name="console", attachment_type=allure.attachment_type.TEXT)
        except Exception:
            pass

    # 3) requestfailed
    if requestfailed_lines and allure is not None:
        try:
            allure.attach("\n".join(requestfailed_lines), name="requestfailed", attachment_type=allure.attachment_type.TEXT)
        except Exception:
            pass

    # 3.5) set-cookie oversize
    if set_cookie_oversize_lines and allure is not None:
        try:
            allure.attach(
                "\n".join(set_cookie_oversize_lines[-50:]),
                name="set_cookie_oversize",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass

    # 4) trace (only for contexts we created)
    if page is not None:
        try:
            ctx = page.context
            trace_path = Path("reports") / f"{test_id}.zip"
            try:
                ctx.tracing.stop(path=str(trace_path))
            except Exception:
                trace_path = None
            if trace_path and trace_path.exists() and allure is not None:
                allure.attach.file(
                    str(trace_path), name="playwright_trace", attachment_type=allure.attachment_type.ZIP
                )
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# TEST DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def test_account(request):
    """
    测试账号 fixture - 每个测试用例使用独立的测试账号
    """
    reuse_login = os.getenv("REUSE_LOGIN", "").strip() in {"1", "true", "True", "yes", "YES"}
    if reuse_login:
        try:
            yield request.getfixturevalue("session_test_account")
            return
        except Exception:
            pass

    test_name = request.node.name
    logger.info(f"🧹 测试前数据清洗: {test_name}")
    data_manager.cleanup_before_test(test_name)

    # 账号可用性预检（避免 UI 登录阶段才发现 invalid/lockout 导致整条用例 setup error）
    backend_url = (config.get_service_url("backend") or "").rstrip("/")
    max_attempts = int(os.getenv("ACCOUNT_ALLOCATE_RETRY", "5"))
    tried = []

    from utils.account_precheck import _abp_cookie_login_and_roles  # type: ignore

    account = None
    for i in range(max_attempts):
        account = data_manager.get_test_account(test_name)
        tried.append(account.get("username"))
        logger.info(f"📦 测试用例 {test_name} 分配账号: {account['username']}")

        # 若缺少 backend_url，则无法预检，直接放行（保持向后兼容）
        if not backend_url:
            break

        identifier = (account.get("email") or account.get("username") or "").strip()
        password = (account.get("password") or "").strip()
        ok, reason, _roles, authenticated = _abp_cookie_login_and_roles(
            backend_url=backend_url,
            identifier=identifier,
            password=password,
        )

        if ok and authenticated:
            break

        # 预检失败：标记账号不可用，释放本用例占用，继续挑下一个
        try:
            data_manager.mark_account_locked(account.get("username"), reason=f"precheck_failed:{reason}")
        except Exception:
            pass
        try:
            data_manager.cleanup_before_test(test_name)
        except Exception:
            pass
        account = None

    if not account:
        pytest.skip(f"没有可用测试账号（预检失败），tried={tried}")

    yield account

    success = True
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        success = False

    logger.info(f"🧹 测试后数据清洗: {test_name} (成功: {success})")
    data_manager.cleanup_after_test(test_name, success=success)


