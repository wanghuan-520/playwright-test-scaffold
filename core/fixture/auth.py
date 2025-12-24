"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Auth session (storage_state) and auth/unauth pages
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import pytest

from core.fixture.shared import (
    _WORKER_SESSION_ACCOUNT,
    _collect_set_cookie_oversize,
    config,
    data_manager,
    logger,
)


# ═══════════════════════════════════════════════════════════════
# LOGIN FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def logged_in_page(page, test_account):
    """已登录的页面 fixture - 自动执行登录流程"""
    from pages.login_page import LoginPage

    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(username=test_account["username"], password=test_account["password"])
    logger.info(f"已登录账号: {test_account['username']}")
    yield page


# ═══════════════════════════════════════════════════════════════
# AUTH SESSION (OIDC/ABP) - Reduce lockout risk
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def xdist_worker_id() -> str:
    """返回 xdist worker id（非并发时返回 'master'）。"""
    return os.getenv("PYTEST_XDIST_WORKER") or "master"


@pytest.fixture(scope="session")
def auth_storage_state_path(xdist_worker_id: str) -> str:
    """
    登录一次并缓存 storage_state。

    目的：
    - 避免每个用例都走 ABP /Account/Login，降低 lockout 风险
    - 加速 P1/P2/security（需要登录态）的执行
    """
    # 并发时每个 worker 用独立 storage_state，避免同一账号/同一 state 跨进程写入冲突。
    return str(Path(".auth") / f"storage_state.{xdist_worker_id}.json")


@pytest.fixture(scope="session")
def ensure_auth_storage_state(browser, auth_storage_state_path: str, xdist_worker_id: str):
    """
    确保已生成登录态 storage_state（session 级别）。
    若无法登录（账号池凭证无效/被锁），则跳过需要登录的用例。
    """
    state_path = Path(auth_storage_state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    reuse_login_env = os.getenv("REUSE_LOGIN", "").strip()
    if reuse_login_env:
        reuse_login = reuse_login_env in {"1", "true", "True", "yes", "YES"}
    else:
        reuse_login = xdist_worker_id != "master"
    reserved_test_name: Optional[str] = None

    # 并发复用登录：只要求“单次运行内复用”，不复用历史 state
    if reuse_login and xdist_worker_id != "master":
        try:
            if state_path.exists():
                state_path.unlink()
        except Exception:
            pass

    # 非复用登录：若已存在且非空，直接复用
    if (not reuse_login) and state_path.exists() and state_path.stat().st_size > 0:
        yield
        return

    def _try_login_with(account: dict) -> tuple[bool, str]:
        identifier = account.get("email") or account.get("username")
        password = account.get("password")
        if not identifier or not password:
            return False, "missing_credentials"

        ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        p = ctx.new_page()
        try:
            oversize_set_cookie_lines = []

            def _on_response(resp):
                try:
                    _collect_set_cookie_oversize(resp.headers, resp.url, resp.status, oversize_set_cookie_lines)
                except Exception:
                    pass

            try:
                ctx.on("response", _on_response)
            except Exception:
                try:
                    p.on("response", _on_response)
                except Exception:
                    pass

            p.goto(f"{config.get_service_url('frontend')}/auth/login", wait_until="domcontentloaded", timeout=30000)
            p.wait_for_selector("#LoginInput_UserNameOrEmailAddress", state="visible", timeout=60000)

            p.fill("#LoginInput_UserNameOrEmailAddress", identifier)
            p.fill("#LoginInput_Password", password)
            p.click("button[name='Action'][type='submit']")

            def _login_error_reason() -> Optional[str]:
                try:
                    if p.get_by_text("Invalid username or password", exact=False).is_visible(timeout=300):
                        return "invalid_credentials"
                except Exception:
                    pass
                try:
                    if p.get_by_text("locked", exact=False).is_visible(timeout=300):
                        return "lockout"
                except Exception:
                    pass
                try:
                    if p.get_by_text("Login failed", exact=False).is_visible(timeout=300):
                        return "login_failed"
                except Exception:
                    pass
                return None

            try:
                p.wait_for_timeout(800)
            except Exception:
                pass
            r0 = _login_error_reason()
            if r0:
                return False, r0

            frontend_url = config.get_service_url("frontend")
            if not frontend_url:
                return False, "missing_frontend_url"

            cfg_json = None
            for _ in range(24):  # ~12s
                try:
                    r = ctx.request.get(f"{frontend_url}/api/abp/application-configuration")
                    if r.status == 200:
                        cfg_json = r.json()
                        cu = (cfg_json.get("currentUser") or {})
                        if cu.get("isAuthenticated") is True:
                            break
                except Exception:
                    pass
                try:
                    p.wait_for_timeout(500)
                except Exception:
                    pass

            if not cfg_json:
                try:
                    r2 = ctx.request.get(f"{frontend_url}/api/account/my-profile")
                    return False, f"abp_cfg_unavailable(my_profile={r2.status})"
                except Exception:
                    return False, "abp_cfg_unavailable"

            current_user = (cfg_json.get("currentUser") or {})
            roles = current_user.get("roles") or []
            roles_l = {str(x).lower() for x in roles}

            profile_path = os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile")
            require_admin = os.getenv("REQUIRE_ADMIN_FOR_ADMIN_PATH", "").strip() in {"1", "true", "True", "yes", "YES"}
            requires_admin = profile_path.startswith("/admin")
            if require_admin and requires_admin and not (roles_l & {"admin", "administrator", "superadmin"}):
                return False, f"not_admin(roles={sorted(list(roles_l))})"

            p.goto(f"{frontend_url}{profile_path}", wait_until="domcontentloaded", timeout=60000)
            try:
                try:
                    p.wait_for_timeout(800)
                except Exception:
                    pass
                if profile_path not in (p.url or ""):
                    return False, f"profile_redirect(url={getattr(p, 'url', '')})"
                p.wait_for_selector("#userName", state="visible", timeout=15000)
            except Exception:
                r1 = _login_error_reason()
                if r1:
                    return False, r1
                return False, f"profile_page_unavailable(url={getattr(p, 'url', '')})"

            if oversize_set_cookie_lines:
                logger.warning("检测到可疑的超大 Set-Cookie（可能导致 iron-session 报错/登录态不稳定）：")
                for line in oversize_set_cookie_lines[-8:]:
                    logger.warning(line)

            ctx.storage_state(path=str(state_path))
            return True, "ok"
        except Exception as e:
            try:
                logger.warning(
                    f"login_attempt_exception: user={account.get('username')} id={identifier} err={type(e).__name__}: {e}",
                    exc_info=True,
                )
            except Exception:
                pass
            return False, f"exception:{type(e).__name__}"
        finally:
            try:
                ctx.close()
            except Exception:
                pass

    if reuse_login:
        test_name = f"__worker_login__{xdist_worker_id}"
        reserved_test_name = test_name
        attempts = 0
        last_username = None
        last_reason: Optional[str] = None
        reason_counts: dict[str, int] = {}

        try:
            data_manager.cleanup_before_test(test_name)
        except Exception:
            pass

        try:
            if xdist_worker_id.startswith("gw"):
                idx = int(xdist_worker_id.replace("gw", "") or "0")
                time.sleep(min(max(idx, 0), 6) * 0.8)
        except Exception:
            pass

        while attempts < 20:
            try:
                acc = data_manager.get_test_account(test_name)
            except RuntimeError:
                try:
                    data_manager.cleanup_before_test(test_name)
                except Exception:
                    pass
                acc = data_manager.get_test_account(test_name)
            last_username = acc.get("username")

            ok, reason = _try_login_with(acc)
            last_reason = reason
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            if ok:
                _WORKER_SESSION_ACCOUNT[xdist_worker_id] = acc
                logger.info(f"✅ worker={xdist_worker_id} 登录态已生成: {state_path} account={acc.get('username')}")
                break

            logger.warning(f"worker={xdist_worker_id} 登录态生成失败，acc={last_username} reason={reason}")
            try:
                data_manager.cleanup_after_test(test_name, success=False)
            except Exception:
                pass

            lock_reason = None
            if reason in {"invalid_credentials", "lockout"}:
                lock_reason = f"login_failed_for_storage_state:{reason}"
            if reason.startswith("profile_redirect(") or reason.startswith("not_admin("):
                lock_reason = f"not_usable_for_profile:{reason}"
            if last_username and lock_reason:
                try:
                    data_manager.mark_account_locked(last_username, reason=lock_reason)
                except Exception:
                    pass
            attempts += 1
            try:
                time.sleep(0.4)
            except Exception:
                pass

        if not (state_path.exists() and state_path.stat().st_size > 0):
            pytest.fail(
                f"无法为 worker={xdist_worker_id} 生成登录态 storage_state（last={last_username} reason={last_reason} reasons={reason_counts}）",
                pytrace=False,
            )

        try:
            yield
        finally:
            try:
                data_manager.cleanup_after_test(test_name, success=True)
            except Exception:
                pass
        return

    if not (state_path.exists() and state_path.stat().st_size > 0):
        data = config.load_test_data("accounts") or {}
        pool = data.get("test_account_pool", [])
        if not pool:
            pytest.skip("账号池为空，无法生成登录态 storage_state")

        for acc in pool:
            ok, reason = _try_login_with(acc)
            if ok:
                logger.info(f"✅ 已生成登录态 storage_state: {state_path}")
                break
            try:
                logger.warning(f"登录态生成失败（非并发模式），acc={acc.get('username')} reason={reason}")
            except Exception:
                pass

    if not (state_path.exists() and state_path.stat().st_size > 0):
        pytest.fail("无法生成登录态 storage_state（可能全部凭证无效/被锁）", pytrace=False)

    yield


@pytest.fixture(scope="session")
def session_test_account(ensure_auth_storage_state, xdist_worker_id: str):
    """复用登录模式下：返回本 worker 的会话账号（与 auth_page 登录态一致）。"""
    acc = _WORKER_SESSION_ACCOUNT.get(xdist_worker_id)
    if not acc:
        pytest.skip("session_test_account not available (no worker session account)")
    return acc


@pytest.fixture(scope="function")
def auth_page(browser, ensure_auth_storage_state, auth_storage_state_path: str):
    """已登录页面（function 级别独立 context）。"""
    ctx = browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        storage_state=auth_storage_state_path,
    )
    try:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        pass
    p = ctx.new_page()
    yield p
    ctx.close()


@pytest.fixture(scope="function")
def unauth_page(browser):
    """未登录页面（function 级别独立 context）。"""
    ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
    try:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        pass
    p = ctx.new_page()
    yield p
    ctx.close()


