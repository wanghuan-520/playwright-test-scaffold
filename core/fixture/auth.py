"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Auth session (storage_state) and auth/unauth pages
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import time
from pathlib import Path
import os
from typing import Optional

import pytest

from core.fixture.shared import (
    _WORKER_SESSION_ACCOUNT,
    _collect_set_cookie_oversize,
    config,
    data_manager,
    logger,
)
from core.fixture.auth_session_login import try_login_with_account


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
        # 重要：历史 storage_state 可能已过期/无效（例如 session/cookie 失效、服务端重启导致会话丢失）。
        # 直接复用会让后续用例卡在页面加载/selector 超时，且难以诊断。
        # 因此这里做一次轻量级验证：能否通过代理接口拿到 my-profile=200。
        try:
            frontend_url = config.get_service_url("frontend")
            if frontend_url:
                ctx = browser.new_context(
                    ignore_https_errors=True,
                    viewport={"width": 1280, "height": 720},
                    storage_state=str(state_path),
                )
                try:
                    r = ctx.request.get(f"{frontend_url}/api/account/my-profile")
                    if r.status == 200:
                        yield
                        return
                finally:
                    try:
                        ctx.close()
                    except Exception:
                        pass
        except Exception:
            # 验证失败（网络/证书等），保守策略：不直接信任旧 state，走重新登录生成
            pass

        # 无效则删除并重新生成
        try:
            state_path.unlink()
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
                # ✅ 使用 "auth" 类型账号（专用于 auth_page + storage_state 链路）
                acc = data_manager.get_test_account(test_name, account_type="auth")
            except RuntimeError:
                try:
                    data_manager.cleanup_before_test(test_name)
                except Exception:
                    pass
                # 账号池已耗尽：直接跳过需要登录态的用例（尤其是 tests/Account 等不应依赖登录态的套件）
                pytest.skip("账号池无可用账号，无法生成登录态 storage_state")
            last_username = acc.get("username")

            ok, reason = try_login_with_account(
                browser=browser,
                config=config,
                logger=logger,
                collect_set_cookie_oversize=_collect_set_cookie_oversize,
                state_path=state_path,
                account=acc,
            )
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
            # profile_redirect/not_admin 更可能是“环境路由/权限策略差异”，不应永久锁死账号池。
            # 只记录日志并继续尝试其它账号，避免并发下把账号池全部标记为不可用。
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
            pytest.skip(
                f"无法为 worker={xdist_worker_id} 生成登录态 storage_state（last={last_username} reason={last_reason} reasons={reason_counts}）"
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
            ok, reason = try_login_with_account(
                browser=browser,
                config=config,
                logger=logger,
                collect_set_cookie_oversize=_collect_set_cookie_oversize,
                state_path=state_path,
                account=acc,
            )
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


