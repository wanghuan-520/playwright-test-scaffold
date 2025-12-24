"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Service checks & environment setup
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from core.fixture.shared import config, logger, _is_tcp_open


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
    # 服务可达性 fail-fast（默认开启）
    # ────────────────────────────────────────────────────────────
    # xdist 下每个 worker 都会跑 session fixture：
    # - 预检如果在每个 worker 都触发 pytest.exit，会表现成 “node down: keyboard-interrupt”，可读性很差
    # - 预检只需要跑一次即可，因此限定在 primary worker 执行
    if is_primary_worker:
        precheck_services = os.getenv("PRECHECK_SERVICES", "").strip()
        if precheck_services.lower() not in {"0", "false", "no"}:
            fe = (config.get_service_url("frontend") or "").rstrip("/")
            be = (config.get_service_url("backend") or "").rstrip("/")
            ok_fe, r_fe = _is_tcp_open(fe)
            ok_be, r_be = _is_tcp_open(be)
            if not ok_fe or not ok_be:
                pytest.exit(
                    "服务不可达（fail-fast）：\n"
                    f"- frontend: {fe or '<empty>'} ({'OK' if ok_fe else 'FAIL'}: {r_fe})\n"
                    f"- backend:  {be or '<empty>'} ({'OK' if ok_be else 'FAIL'}: {r_be})\n"
                    "请先启动服务或修正 config/project.yaml 的 environments.<env>.{frontend,backend}.url。\n"
                    "如确需跳过该检查：设置 PRECHECK_SERVICES=0。",
                    returncode=2,
                )

    # ────────────────────────────────────────────────────────────
    # 账号池预检（可选，使用后端接口，速度更快）
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
            # fail-fast：预检已明确没有足够可用账号时，直接停止
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


