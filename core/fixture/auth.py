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
            
            # 个人设置路径白名单：这些 /admin/* 路径不需要 admin 角色
            # 任何登录用户都可以访问自己的个人资料和修改密码
            PERSONAL_PATHS = {
                "/admin/profile",
                "/admin/profile/change-password",
            }
            
            # 只有非个人路径的 /admin/* 才需要 admin 角色
            requires_admin = (
                profile_path.startswith("/admin") 
                and profile_path not in PERSONAL_PATHS
            )

            # 默认策略：只要走 /admin/*（排除个人路径），就要求 admin 账号
            # 如需允许普通账号访问其他 /admin 路径：显式设置 REQUIRE_ADMIN_FOR_ADMIN_PATH=0
            require_admin_env = os.getenv("REQUIRE_ADMIN_FOR_ADMIN_PATH", "").strip()
            if require_admin_env:
                require_admin = require_admin_env in {"1", "true", "True", "yes", "YES"}
            else:
                require_admin = requires_admin
            if require_admin and requires_admin and not (roles_l & {"admin", "administrator", "superadmin"}):
                return False, f"not_admin(roles={sorted(list(roles_l))})"

            def _verify_session_via_my_profile() -> tuple[bool, str]:
                """
                用后端/代理接口验证登录态是否真正生效。

                为什么：
                - 页面路由可能因产品策略（/admin 权限、首登引导、A/B）发生跳转
                - 但 storage_state 的本质是 cookies/session 是否可用，最稳定的验证是 my-profile 200
                """
                try:
                    r = ctx.request.get(f"{frontend_url}/api/account/my-profile")
                    if r.status == 200:
                        return True, "ok"
                    return False, f"my_profile_not_ok(status={r.status})"
                except Exception as e:
                    return False, f"my_profile_exception({type(e).__name__})"

            # 先做一次接口级验证（避免被页面跳转误判为“未登录”）
            ok_my, reason_my = _verify_session_via_my_profile()
            if not ok_my:
                return False, f"login_state_unstable({reason_my})"

            # 再尝试访问 profile 页面（用于提前发现路由/权限问题），但这里不再作为 storage_state 生成的硬门槛
            p.goto(f"{frontend_url}{profile_path}", wait_until="domcontentloaded", timeout=60000)
            try:
                try:
                    p.wait_for_timeout(800)
                except Exception:
                    pass
                if profile_path not in (p.url or ""):
                    # 关键：不要因为“页面跳转策略”直接让 storage_state 生成失败，否则会导致整套登录态用例全部 skip。
                    # 具体页面可访问性由对应的 UI 用例断言。
                    logger.warning(f"storage_state: profile page redirected, url={getattr(p, 'url', '')}")
                p.wait_for_selector("#userName", state="visible", timeout=15000)
            except Exception:
                r1 = _login_error_reason()
                if r1:
                    return False, r1
                # profile 页面不可用仍允许生成 storage_state（原因同上）
                logger.warning(f"storage_state: profile page unavailable, url={getattr(p, 'url', '')}")

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


