"""
Auth storage_state 登录态构建辅助函数。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def try_login_with_account(
    *,
    browser,
    config,
    logger,
    collect_set_cookie_oversize,
    state_path: Path,
    account: dict,
) -> tuple[bool, str]:
    """
    使用指定账号登录并落盘 storage_state。
    返回 (success, reason)。
    """
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
                collect_set_cookie_oversize(resp.headers, resp.url, resp.status, oversize_set_cookie_lines)
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
        for _ in range(24):
            try:
                r = ctx.request.get(f"{frontend_url}/api/abp/application-configuration")
                if r.status == 200:
                    cfg_json = r.json()
                    cu = cfg_json.get("currentUser") or {}
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

        current_user = cfg_json.get("currentUser") or {}
        roles = current_user.get("roles") or []
        roles_l = {str(x).lower() for x in roles}

        profile_path = os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile")
        personal_paths = {"/admin/profile", "/admin/profile/change-password"}
        requires_admin = profile_path.startswith("/admin") and profile_path not in personal_paths

        require_admin_env = os.getenv("REQUIRE_ADMIN_FOR_ADMIN_PATH", "").strip()
        if require_admin_env:
            require_admin = require_admin_env in {"1", "true", "True", "yes", "YES"}
        else:
            require_admin = requires_admin

        if require_admin and requires_admin and not (roles_l & {"admin", "administrator", "superadmin"}):
            return False, f"not_admin(roles={sorted(list(roles_l))})"

        try:
            r = ctx.request.get(f"{frontend_url}/api/account/my-profile")
            if r.status != 200:
                return False, f"login_state_unstable(my_profile_not_ok(status={r.status}))"
        except Exception as e:
            return False, f"login_state_unstable(my_profile_exception({type(e).__name__}))"

        p.goto(f"{frontend_url}{profile_path}", wait_until="domcontentloaded", timeout=60000)
        try:
            try:
                p.wait_for_timeout(800)
            except Exception:
                pass
            if profile_path not in (p.url or ""):
                logger.warning(f"storage_state: profile page redirected, url={getattr(p, 'url', '')}")
            p.wait_for_selector("#userName", state="visible", timeout=15000)
        except Exception:
            r1 = _login_error_reason()
            if r1:
                return False, r1
            logger.warning(f"storage_state: profile page unavailable, url={getattr(p, 'url', '')}")

        if oversize_set_cookie_lines:
            logger.warning("检测到可疑的超大 Set-Cookie（可能导致登录态不稳定）：")
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
