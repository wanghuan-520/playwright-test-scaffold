# ═══════════════════════════════════════════════════════════════
# Admin Tests - Conftest (Admin Account & Environment)
# ═══════════════════════════════════════════════════════════════
"""
Admin 测试专用配置

关键设置：
- PERSONAL_SETTINGS_PATH: 设置为 /admin/users（需要 admin 角色）
- REQUIRE_ADMIN_FOR_ADMIN_PATH: 明确要求 admin 账号

账号要求：
- 使用 account_type="admin" 的账号（TestAdmin1~10）
"""

import os
import pytest
from playwright.sync_api import Page

# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP (MODULE LEVEL)
# ═══════════════════════════════════════════════════════════════

# 设置 admin 页面路径，确保使用 admin 账号
os.environ["PERSONAL_SETTINGS_PATH"] = "/admin/users"
os.environ["REQUIRE_ADMIN_FOR_ADMIN_PATH"] = "1"
os.environ["ADMIN_ACCOUNT_TYPE"] = "admin"


# ═══════════════════════════════════════════════════════════════
# ADMIN AUTH FIXTURE
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def admin_storage_state_path(xdist_worker_id: str) -> str:
    """Admin 登录态文件路径（与普通用户分开）"""
    from pathlib import Path
    return str(Path(".auth") / f"admin_storage_state.{xdist_worker_id}.json")


@pytest.fixture(scope="session")
def ensure_admin_storage_state(browser, admin_storage_state_path: str, xdist_worker_id: str):
    """
    确保 admin 登录态存在（使用 admin 账号登录）
    """
    import time
    from pathlib import Path
    from core.fixture.shared import config, data_manager, logger
    
    state_path = Path(admin_storage_state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 每次运行清理旧 state
    try:
        if state_path.exists():
            state_path.unlink()
    except Exception:
        pass
    
    def _try_admin_login(account: dict) -> tuple[bool, str]:
        """尝试使用 admin 账号登录"""
        identifier = account.get("email") or account.get("username")
        password = account.get("password")
        if not identifier or not password:
            return False, "missing_credentials"
        
        ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        p = ctx.new_page()
        try:
            frontend_url = config.get_service_url('frontend')
            
            # React 前端登录
            p.goto(f"{frontend_url}/login", wait_until="domcontentloaded", timeout=30000)
            
            is_react_login = p.locator('input[placeholder="Enter username or email"]').count() > 0
            
            if is_react_login:
                p.fill('input[placeholder="Enter username or email"]', identifier)
                p.fill('input[placeholder="Enter your password"]', password)
                p.click('button:has-text("Sign In")')
            else:
                # ABP 后端风格
                p.goto(f"{frontend_url}/auth/login", wait_until="domcontentloaded", timeout=30000)
                p.wait_for_selector("#LoginInput_UserNameOrEmailAddress", state="visible", timeout=60000)
                p.fill("#LoginInput_UserNameOrEmailAddress", identifier)
                p.fill("#LoginInput_Password", password)
                p.click("button[name='Action'][type='submit']")
            
            # 等待登录完成
            p.wait_for_timeout(2000)
            
            # 检查登录错误
            try:
                if p.get_by_text("Invalid username or password", exact=False).is_visible(timeout=300):
                    return False, "invalid_credentials"
            except Exception:
                pass
            
            # 验证登录态（使用页面内 fetch 替代 ctx.request，避免 ECONNREFUSED）
            cfg_json = None
            last_err = None
            for attempt in range(20):
                try:
                    result = p.evaluate("""async () => {
                        try {
                            const r = await fetch('/api/abp/application-configuration');
                            if (!r.ok) return { error: 'status_' + r.status };
                            const data = await r.json();
                            const cu = data.currentUser || {};
                            return { isAuthenticated: !!cu.isAuthenticated, roles: cu.roles || [] };
                        } catch(e) {
                            return { error: e.message };
                        }
                    }""")
                    if result.get("error"):
                        last_err = result["error"]
                    elif result.get("isAuthenticated"):
                        cfg_json = result
                        break
                except Exception as e:
                    last_err = f"{type(e).__name__}: {e}"
                p.wait_for_timeout(500)
            
            if not cfg_json:
                page_url = p.url if p else "unknown"
                return False, f"abp_cfg_unavailable(last_err={last_err}, page_url={page_url})"
            
            # 验证 admin 角色
            roles = cfg_json.get("roles") or []
            roles_l = {str(x).lower() for x in roles}
            
            if not (roles_l & {"admin", "administrator", "superadmin"}):
                return False, f"not_admin(roles={sorted(list(roles_l))})"
            
            # 保存 storage_state
            ctx.storage_state(path=str(state_path))
            return True, "ok"
            
        except Exception as e:
            return False, f"exception:{type(e).__name__}"
        finally:
            try:
                ctx.close()
            except Exception:
                pass
    
    # 从账号池获取 admin 账号
    test_name = f"__admin_login__{xdist_worker_id}"
    attempts = 0
    last_reason = None
    
    # 等待避免并发冲突
    try:
        if xdist_worker_id.startswith("gw"):
            idx = int(xdist_worker_id.replace("gw", "") or "0")
            time.sleep(min(max(idx, 0), 6) * 0.5)
    except Exception:
        pass
    
    while attempts < 10:
        try:
            # 使用 admin 账号类型
            acc = data_manager.get_test_account(test_name, account_type="admin")
        except RuntimeError as e:
            pytest.skip(f"无可用 admin 账号：{e}")
        
        ok, reason = _try_admin_login(acc)
        last_reason = reason
        
        if ok:
            logger.info(f"✅ Admin 登录态已生成: {state_path} account={acc.get('username')}")
            yield
            try:
                data_manager.cleanup_after_test(test_name, success=True)
            except Exception:
                pass
            return
        
        logger.warning(f"Admin 登录失败: acc={acc.get('username')} reason={reason}")
        try:
            data_manager.cleanup_after_test(test_name, success=False)
        except Exception:
            pass
        
        attempts += 1
        time.sleep(0.5)
    
    pytest.skip(f"无法生成 Admin 登录态 (last_reason={last_reason})")


@pytest.fixture(scope="function")
def auth_page(browser, ensure_admin_storage_state, admin_storage_state_path: str):
    """
    Admin 已登录页面（覆盖 core 的 auth_page）
    
    重要：这个 fixture 覆盖了 core/fixture/auth.py 中的 auth_page，
    确保 admin 测试使用 admin 账号的 storage_state。
    """
    ctx = browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        storage_state=admin_storage_state_path,
    )
    try:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        pass
    p = ctx.new_page()
    yield p
    ctx.close()

