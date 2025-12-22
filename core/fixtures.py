# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Pytest Fixtures
# ═══════════════════════════════════════════════════════════════
"""
通用测试 fixtures - 提供测试所需的各种资源
"""

import pytest
import os
import shutil
import time
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, BrowserContext
from utils.config import ConfigManager
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)
config = ConfigManager()
data_manager = DataManager()

# 每个 xdist worker 进程内的“会话账号”（用于复用登录态/避免并发互相覆盖 Profile 数据）
_WORKER_SESSION_ACCOUNT = {}


# ═══════════════════════════════════════════════════════════════
# DIAGNOSTICS - Cookie oversize (iron-session etc.)
# ═══════════════════════════════════════════════════════════════

def _collect_set_cookie_oversize(headers: dict, url: str, status: int, out_lines: list, warn_bytes: int = 3800) -> None:
    """
    记录可疑的 Set-Cookie 体积（接近/超过 4KB 上限时浏览器会拒绝）。

    背景：
    - 一些框架（例如 Next.js + iron-session）会把 session 序列化后放进 cookie
    - 浏览器对单个 cookie 有约 4096 bytes 的限制，超过会被拒绝或截断
    """
    try:
        # Playwright Python: response.headers 是 dict，键通常为小写
        set_cookie = headers.get("set-cookie") or headers.get("Set-Cookie")
        if not set_cookie:
            return

        # set_cookie 可能是一个很长的字符串；用 utf-8 估算字节数更接近浏览器限制
        size = len(set_cookie.encode("utf-8", errors="ignore"))
        if size < warn_bytes:
            return

        # 尝试提取 cookie 名称（不保证 100% 准确，但足够定位）
        cookie_name = ""
        try:
            cookie_name = (set_cookie.split("=", 1)[0] or "").strip()
        except Exception:
            cookie_name = ""

        preview = set_cookie[:220].replace("\n", "\\n").replace("\r", "\\r")
        out_lines.append(
            f"[set-cookie-oversize] bytes={size} status={status} cookie={cookie_name} url={url} preview={preview}..."
        )
    except Exception:
        # 诊断逻辑永远不能影响测试主流程
        return


# ═══════════════════════════════════════════════════════════════
# BROWSER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """配置浏览器上下文参数"""
    browser_config = config.get_browser_config()
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {
            "width": browser_config.get("viewport_width", 1920),
            "height": browser_config.get("viewport_height", 1080)
        },
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """配置浏览器启动参数"""
    browser_config = config.get_browser_config()
    args = config.get("browser.args", [])
    return {
        **browser_type_launch_args,
        "headless": browser_config.get("headless", True),
        "slow_mo": browser_config.get("slow_mo", 0),
        "timeout": 60000,
        "args": args if args else [
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--allow-insecure-localhost",
            "--disable-gpu",
            "--no-sandbox",
        ],
    }


# ═══════════════════════════════════════════════════════════════
# PAGE FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def test_page(page: Page) -> Page:
    """测试页面 fixture - 每个测试独立的页面实例"""
    logger.info("创建测试页面")
    yield page
    logger.info("关闭测试页面")


@pytest.fixture(scope="class")
def shared_page(browser) -> Page:
    """共享页面 fixture - 测试类内共享"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    logger.info("创建共享页面")
    yield page
    logger.info("关闭共享页面")
    context.close()


# ═══════════════════════════════════════════════════════════════
# SERVICE URL FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def frontend_url() -> str:
    """获取前端服务 URL"""
    return config.get_service_url("frontend")


@pytest.fixture(scope="session")
def backend_url() -> str:
    """获取后端服务 URL"""
    return config.get_service_url("backend")


@pytest.fixture(scope="session")
def current_environment() -> str:
    """获取当前环境名称"""
    return config.get_environment()


# ═══════════════════════════════════════════════════════════════
# TEST DATA FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_config():
    """测试配置 fixture"""
    return config


@pytest.fixture(scope="session")
def accounts_pool():
    """测试账号池 fixture - 获取完整账号池"""
    data = config.load_test_data("accounts")
    if data and "test_account_pool" in data:
        return data["test_account_pool"]
    return []


@pytest.fixture(scope="function")
def test_data():
    """
    通用测试数据加载器 fixture
    
    使用方式:
        def test_xxx(test_data):
            orders = test_data("orders")
            products = test_data("products")
    """
    def _load_data(name: str):
        return config.load_test_data(name)
    return _load_data


# ═══════════════════════════════════════════════════════════════
# LOGIN FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def logged_in_page(page: Page, test_account) -> Page:
    """已登录的页面 fixture - 自动执行登录流程"""
    from pages.login_page import LoginPage
    
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(
        username=test_account["username"],
        password=test_account["password"]
    )
    logger.info(f"已登录账号: {test_account['username']}")
    yield page


# ═══════════════════════════════════════════════════════════════
# SERVICE CHECK FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def service_checker():
    """服务检查器 fixture"""
    from utils.service_checker import ServiceChecker
    return ServiceChecker()


@pytest.fixture(scope="session", autouse=False)
def ensure_services_running(service_checker):
    """
    确保服务运行 fixture（非自动）
    
    使用方式:
        @pytest.mark.usefixtures("ensure_services_running")
        class TestXxx:
            pass
    """
    if not service_checker.is_enabled():
        logger.info("服务健康检查已禁用")
        return
    
    report = service_checker.get_status_report()
    print(report)
    
    results = service_checker.check_all_services()
    failed = [name for name, (ok, _) in results.items() if not ok]
    
    if failed:
        pytest.skip(f"服务不可用: {', '.join(failed)}")


# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境 - session 级别"""
    # xdist 并发下：每个 worker 都会执行 session 级 fixture。
    # 如果每个 worker 都 rm -rf allure-results/screenshots，会互相踩踏，导致进度卡住/报告丢失。
    worker = os.getenv("PYTEST_XDIST_WORKER")  # e.g. gw0/gw1/...；非 xdist 时为 None
    is_primary_worker = (worker is None) or (worker == "gw0")
    ready_flag = Path(".tmp_env_ready")

    # APPEND_ALLURE_RESULTS=1：追加模式（允许“分段跑”后汇总一个报告）
    # - 不清空 allure-results / screenshots / allure-report
    # - 仅确保目录存在
    append_results = os.getenv("APPEND_ALLURE_RESULTS", "").strip() in {"1", "true", "True", "yes", "YES"}

    # 规则要求：每次 pytest 运行都必须从“干净状态”开始，避免 Allure 结果混入历史。
    # 如需保留历史趋势（allure-results/history），设置环境变量：
    #   KEEP_ALLURE_HISTORY=1
    keep_history = os.getenv("KEEP_ALLURE_HISTORY", "").strip() in {"1", "true", "True", "yes", "YES"}

    allure_results = Path("allure-results")
    allure_report = Path("allure-report")
    screenshots = Path("screenshots")

    history_tmp: Path = Path(".tmp_allure_history")
    if append_results:
        # 追加模式：只确保目录存在，不做清理/等待
        os.makedirs("reports", exist_ok=True)
        os.makedirs("allure-results", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        logger.info("🧩 APPEND_ALLURE_RESULTS=1：追加模式启用（不清空历史结果）")
        yield
        return

    if is_primary_worker:
        # primary worker 负责“清场”
        try:
            if ready_flag.exists():
                ready_flag.unlink()
        except Exception:
            pass

        if keep_history and (allure_results / "history").exists():
            history_tmp.mkdir(parents=True, exist_ok=True)
            # 保存一份 history，避免 rm -rf 直接丢失趋势
            shutil.rmtree(history_tmp, ignore_errors=True)
            shutil.copytree(allure_results / "history", history_tmp)

        # 仅 primary worker 清理目录，避免并发互删
        shutil.rmtree(allure_results, ignore_errors=True)
        shutil.rmtree(allure_report, ignore_errors=True)
        shutil.rmtree(screenshots, ignore_errors=True)
    else:
        # 非 primary worker 等待清场完成，避免“别人刚写入 allure-results 又被 gw0 删掉”
        deadline = time.time() + 60
        while time.time() < deadline:
            if ready_flag.exists():
                break
            time.sleep(0.2)

    # 重建目录
    os.makedirs("reports", exist_ok=True)
    os.makedirs("allure-results", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)

    # ────────────────────────────────────────────────────────────
    # 账号池预检（可选，使用后端接口，速度更快）
    #
    # 用途：在并发跑之前，把“无效账号/非 admin 账号”提前标记出来，避免 setup 阶段盲撞。
    # 开关：PRECHECK_ACCOUNTS=1
    # 需要：REUSE_LOGIN=1（并发复用登录模式）
    # 说明：默认走 ABP 的 /api/account/login（cookie）+ /api/abp/application-configuration（roles）
    # ────────────────────────────────────────────────────────────
    precheck_enabled = os.getenv("PRECHECK_ACCOUNTS", "").strip() in {"1", "true", "True", "yes", "YES"}
    reuse_login = os.getenv("REUSE_LOGIN", "").strip() in {"1", "true", "True", "yes", "YES"}
    if is_primary_worker and precheck_enabled and reuse_login:
        summary = None
        need = int(os.getenv("PRECHECK_NEED", "4") or "4")
        try:
            from utils.account_precheck import precheck_account_pool

            summary = precheck_account_pool(
                frontend_url=(config.get_service_url("frontend") or "").rstrip("/"),
                backend_url=(config.get_service_url("backend") or "").rstrip("/"),
                personal_settings_path=os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile"),
                need_usable=max(need, 0),
                update_pool=True,
                lock_not_admin=True,
            )
            logger.info(f"✅ 账号池预检完成: {summary}")
        except Exception as e:
            # pytest.exit 会抛出 Exit（属于 Exception），必须放行，避免被“忽略不阻塞运行”的逻辑吞掉。
            if e.__class__.__name__ in {"Exit", "SystemExit"}:
                raise
            # 预检失败不应中断整个测试（否则会影响本地开发），但会在日志里暴露原因
            logger.warning(f"账号池预检失败（已忽略，不阻塞运行）: {type(e).__name__}: {e}")
        else:
            # fail-fast：预检已明确没有足够可用账号时，直接停止，避免后续 worker 在 setup 阶段盲撞/触发 lockout
            usable = int((summary or {}).get("usable") or 0)
            if need > 0 and usable < need:
                pytest.exit(
                    f"账号池预检失败：可用账号 {usable} < 需要 {need}。"
                    f"（invalid_credentials / not_admin / lockout 等原因见日志）"
                    f"请补充可登录的 admin 账号，或调整 PERSONAL_SETTINGS_PATH，"
                    f"或设置 PRECHECK_NEED=0 关闭 fail-fast。",
                    returncode=2,
                )

    if is_primary_worker:
        if keep_history and history_tmp.exists():
            (allure_results / "history").mkdir(parents=True, exist_ok=True)
            # copytree 需要目标不存在，因此逐文件复制
            for p in history_tmp.rglob("*"):
                if p.is_dir():
                    continue
                rel = p.relative_to(history_tmp)
                target = allure_results / "history" / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
            shutil.rmtree(history_tmp, ignore_errors=True)

        # 发出“环境就绪”信号
        try:
            ready_flag.write_text("ready", encoding="utf-8")
        except Exception:
            pass
    
    logger.info("=" * 60)
    logger.info("🚀 测试环境初始化完成")
    logger.info(f"   环境: {config.get_environment()}")
    logger.info(f"   前端: {config.get_service_url('frontend')}")
    logger.info(f"   后端: {config.get_service_url('backend')}")
    logger.info("=" * 60)
    
    yield
    
    logger.info("=" * 60)
    logger.info("🏁 测试执行完成")
    logger.info("=" * 60)


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

    # 并发（xdist）下必须启用“每 worker 独立账号 + 复用登录态”的模式，否则会出现：
    # - 多进程同时生成 storage_state 竞态
    # - 多 worker 共用同一账号导致 profile 数据互相覆盖
    # 默认策略：
    # - xdist worker（gw*）默认启用 REUSE_LOGIN
    # - master（非并发）默认不启用（复用已有 storage_state 即可）
    reuse_login_env = os.getenv("REUSE_LOGIN", "").strip()
    if reuse_login_env:
        reuse_login = reuse_login_env in {"1", "true", "True", "yes", "YES"}
    else:
        reuse_login = xdist_worker_id != "master"
    reserved_test_name: Optional[str] = None

    # 并发复用登录：只要求“单次运行内复用”，不复用历史 state（避免 worker 复用到同一账号导致互相覆盖）
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
            # --- Cookie 体积探针：定位哪个响应把 cookie 撑爆 ---
            oversize_set_cookie_lines = []

            def _on_response(resp):
                try:
                    _collect_set_cookie_oversize(resp.headers, resp.url, resp.status, oversize_set_cookie_lines)
                except Exception:
                    pass

            try:
                # 用 context 监听能覆盖所有页面/重定向链路
                ctx.on("response", _on_response)
            except Exception:
                # fallback：某些版本也可用 page.on
                try:
                    p.on("response", _on_response)
                except Exception:
                    pass

            # /auth/login 会重定向到后端 /Account/Login
            # 并发下偶发前端抖动会导致 goto 卡满 60s，拖垮整套并发跑；缩短单次超时并依靠重试兜底。
            p.goto(f"{config.get_service_url('frontend')}/auth/login", wait_until="domcontentloaded", timeout=30000)
            p.wait_for_selector("#LoginInput_UserNameOrEmailAddress", state="visible", timeout=60000)

            p.fill("#LoginInput_UserNameOrEmailAddress", identifier)
            p.fill("#LoginInput_Password", password)
            p.click("button[name='Action'][type='submit']")

            # --- 失败分类：只在“明确凭证问题/锁定”时锁账号；不要用超时/偶发波动误伤账号池 ---
            def _login_error_reason() -> Optional[str]:
                # ABP 常见提示（尽量宽松匹配，避免绑死文案）
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

            # 给后端一点点时间返回错误/跳转（不要长等 networkidle，CI/本机都容易抖）
            try:
                p.wait_for_timeout(800)
            except Exception:
                pass
            r0 = _login_error_reason()
            if r0:
                return False, r0

            # --- 登录态判定：用 ABP application-configuration 做“可检证”的硬判定 ---
            # 这里要“轮询”而不是一次性请求：cookie 写入 + 重定向链路在并发/慢机下会抖。
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
                # 兜底：再试一次 my-profile，区分“完全未登录” vs “ABP 配置接口不可用”
                try:
                    r2 = ctx.request.get(f"{frontend_url}/api/account/my-profile")
                    return False, f"abp_cfg_unavailable(my_profile={r2.status})"
                except Exception:
                    return False, "abp_cfg_unavailable"

            current_user = (cfg_json.get("currentUser") or {})
            roles = current_user.get("roles") or []
            roles_l = {str(x).lower() for x in roles}

            # --- 权限判定：以实际环境为准（默认不强制 admin） ---
            profile_path = os.getenv("PERSONAL_SETTINGS_PATH", "/admin/profile")
            require_admin = os.getenv("REQUIRE_ADMIN_FOR_ADMIN_PATH", "").strip() in {"1", "true", "True", "yes", "YES"}
            requires_admin = profile_path.startswith("/admin")
            if require_admin and requires_admin and not (roles_l & {"admin", "administrator", "superadmin"}):
                return False, f"not_admin(roles={sorted(list(roles_l))})"

            # --- 目标页面可用性：只有能打开 Personal Settings，才算“可用于本目录用例”的账号 ---
            p.goto(f"{frontend_url}{profile_path}", wait_until="domcontentloaded", timeout=60000)
            try:
                # 先快速判断是否被重定向（无权限/路由不存在）
                try:
                    p.wait_for_timeout(800)
                except Exception:
                    pass
                if profile_path not in (p.url or ""):
                    return False, f"profile_redirect(url={getattr(p, 'url', '')})"

                p.wait_for_selector("#userName", state="visible", timeout=15000)
            except Exception:
                # 如果没到 profile，优先判断是否仍在登录页/鉴权失败
                r1 = _login_error_reason()
                if r1:
                    return False, r1
                # 兜底：记录当前 url，方便排查（但不要锁账号）
                return False, f"profile_page_unavailable(url={getattr(p, 'url', '')})"

            if oversize_set_cookie_lines:
                # 登录成功但 cookie 体积已接近上限，提前给出定位线索（避免只在 Allure 里看到一句 iron-session 报错）
                logger.warning("检测到可疑的超大 Set-Cookie（可能导致 iron-session 报错/登录态不稳定）：")
                for line in oversize_set_cookie_lines[-8:]:
                    logger.warning(line)

            # 导出 storage state
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

    # 并发复用登录：每个 worker 需要“自己的登录账号”，否则 profile 数据会互相覆盖。
    # 这里从账号池中动态找一个能登录的账号，并保留到 session 结束。
    if reuse_login:
        test_name = f"__worker_login__{xdist_worker_id}"
        reserved_test_name = test_name
        attempts = 0
        last_username = None
        last_reason: Optional[str] = None
        reason_counts: dict[str, int] = {}

        # --- 关键：并发复用登录模式下，必须在“会话登录态生成前”做一次账号池自愈 ---
        # 否则历史运行把账号标记为 is_locked 后（例如 login_failed_for_storage_state），后续 runs 会出现：
        #   - 总账号数充足，但可用账号=0 → worker 直接报错，整套并发跑不起来
        # cleanup_before_test 会：
        #   - 释放残留 in_use（超过阈值）
        #   - 解锁 is_locked（清理 locked_reason）
        # 且不会把其它 worker 正在使用的账号（in_use=True, 未过期）强行释放。
        try:
            data_manager.cleanup_before_test(test_name)
        except Exception:
            pass

        # --- 关键：错峰登录，避免 4 worker 同时打 /Account/Login 导致偶发 lockout / 资源争用 ---
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
                # 兜底：如果没有可用账号，再做一次自愈并重试一次
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

            logger.warning(
                f"worker={xdist_worker_id} 登录态生成失败，acc={last_username} reason={reason}"
            )

            # 登录失败：释放账号，并标记为不可用（避免每个 worker 反复踩同一个坏账号）
            try:
                data_manager.cleanup_after_test(test_name, success=False)
            except Exception:
                pass
            # 只有在“明确不可用”的场景才锁账号：
            # - invalid_credentials/lockout：账号本身坏
            # - profile_redirect/not_admin：该账号无权限访问 /admin/profile（对本目录用例不可用）
            # 超时/偶发异常不锁，避免把好账号误伤成 0 可用
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
            # session 结束释放账号
            try:
                data_manager.cleanup_after_test(test_name, success=True)
            except Exception:
                pass
        return

    # 非复用登录：如果 state 不存在则尝试一次（不持有账号池的 in_use，不做并发安全保证）
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
        # 这里是“测试前置条件失败”，继续 skip 会让用户误以为用例没跑。
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
    """
    已登录页面（function 级别独立 context）。
    
    使用方式：
        def test_xxx(self, auth_page): ...
    """
    ctx = browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        storage_state=auth_storage_state_path,
    )
    # 失败诊断：开启 trace（仅在失败时落盘并附加到 Allure）
    try:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    except Exception:
        # 某些环境 tracing 可能不可用；不阻塞测试执行
        pass
    p = ctx.new_page()
    yield p
    # teardown：context 关闭在 artifacts fixture 之后执行即可
    ctx.close()


# ═══════════════════════════════════════════════════════════════
# TEST LOGGING
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def log_test_info(request):
    """自动记录测试信息"""
    test_name = request.node.name
    test_file = request.node.fspath.basename if hasattr(request.node, 'fspath') else ""
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"▶️  开始测试: {test_file}::{test_name}")
    logger.info("=" * 60)
    
    yield
    
    logger.info(f"⏹️  结束测试: {test_name}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT ON FAILURE
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
    # 运行期收集 console/network 信息
    console_lines = []
    requestfailed_lines = []
    set_cookie_oversize_lines = []

    def _get_page():
        # 优先 auth_page（本项目默认需要登录态），否则回退到 playwright 的 page
        for name in ("auth_page", "page", "test_page", "logged_in_page"):
            try:
                return request.getfixturevalue(name)
            except Exception:
                continue
        return None

    page = _get_page()
    if page is not None:
        try:
            page.on("console", lambda m: console_lines.append(f"[{m.type}] {m.text}"))
            # Playwright Python: request.failure 通常是 Optional[str]（error text），不是对象。
            # 这里必须容错，否则 event listener 异常会污染整个测试过程。
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

            # --- 额外诊断：抓取超大 Set-Cookie（iron-session 报错常见根因） ---
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

    # 尝试导入 allure（可选）
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
                allure.attach.file(str(screenshot_path), name="failure_screenshot", attachment_type=allure.attachment_type.PNG)
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

    # 4) trace (only for auth_page contexts we created)
    if page is not None:
        try:
            ctx = page.context
            trace_path = Path("reports") / f"{test_id}.zip"
            try:
                ctx.tracing.stop(path=str(trace_path))
            except Exception:
                # tracing may not have been started
                trace_path = None
            if trace_path and trace_path.exists() and allure is not None:
                allure.attach.file(str(trace_path), name="playwright_trace", attachment_type=allure.attachment_type.ZIP)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# TEST DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def test_account(request):
    """
    测试账号 fixture - 每个测试用例使用独立的测试账号
    
    功能:
    1. 测试前: 自动清理账号状态（解锁、重置）
    2. 测试中: 为测试用例分配独立的测试账号
    3. 测试后: 自动清理账号状态（释放、恢复）
    
    使用方式:
        def test_xxx(self, page, test_account):
            username = test_account["username"]
            password = test_account["password"]
    """
    # 并发 + 复用登录：不要每条用例都去账号池抢账号（会造成多进程竞争与账号耗尽）
    reuse_login = os.getenv("REUSE_LOGIN", "").strip() in {"1", "true", "True", "yes", "YES"}
    if reuse_login:
        # 统一使用 worker session account（与 auth_page 登录态一致）
        try:
            yield request.getfixturevalue("session_test_account")
            return
        except Exception:
            # fallback：如果没有 worker_login_account，就退回到原逻辑
            pass

    test_name = request.node.name
    
    # 测试前数据清洗
    logger.info(f"🧹 测试前数据清洗: {test_name}")
    data_manager.cleanup_before_test(test_name)
    
    # 分配测试账号
    account = data_manager.get_test_account(test_name)
    logger.info(f"📦 测试用例 {test_name} 分配账号: {account['username']}")
    
    yield account
    
    # 测试后数据清洗
    success = True
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        success = False
    
    logger.info(f"🧹 测试后数据清洗: {test_name} (成功: {success})")
    data_manager.cleanup_after_test(test_name, success=success)
