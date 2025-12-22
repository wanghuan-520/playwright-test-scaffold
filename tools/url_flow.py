"""
# ═══════════════════════════════════════════════════════════════
# URL Flow Runner (mandatory analysis + generation)
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 把“页面分析 + 全量生成”从规范变成“默认必选的可执行入口”
# - 一条命令完成：分析 → 生成 → 清理 → pytest → allure 报告（可选）
#
# 设计原则：
# - 不引入新依赖（复用现有 click / generators / pytest.ini）
# - 失败可检证（打印关键路径与命令）
# - 运行产物不入库（由 .gitignore 覆盖）
#
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import json
from pathlib import Path
from typing import List, Optional

import click

from generators.page_analyzer import PageAnalyzer
from generators.test_code_generator import TestCodeGenerator
from generators.page_types import page_info_from_dict
from generators.utils import extract_url_path
from utils.rules_loader import load_rules_context, write_rules_context
from utils.rules_engine import get_rules_config


def _rm(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _clean_artifacts(root: Path) -> None:
    # 这些目录全部是运行产物：删了只会让下次重建
    for p in [
        root / "allure-results",
        root / "allure-report",
        root / "screenshots",
        root / "reports",  # pytest.log / 自定义日志
        root / ".pytest_cache",
    ]:
        _rm(p)


def _run(cmd: List[str], *, cwd: Path, check: bool = True) -> int:
    click.echo(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd))
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode


def _infer_suite_dir_from_url(url: str) -> str:
    """
    默认把当前 URL 映射到生成套件目录，避免 pytest 扫全 tests/。

    约定：tests/<module>/<page>
    - module: URL 第一段
    - page: URL 从第二段开始的全部 path 用 '_' 拼接，且 '-' -> '_'
      例：/admin/profile/change-password -> tests/admin/profile_change_password
    """
    url_path = extract_url_path(url)
    segments = [s for s in url_path.strip("/").split("/") if s]
    if not segments:
        return "tests/root/home"
    module = segments[0]
    page_parts = segments[1:] if len(segments) > 1 else [segments[0]]
    safe_parts = [(p or "").replace("-", "_") for p in page_parts if p]
    page = "_".join(safe_parts) if safe_parts else (segments[1] if len(segments) > 1 else segments[0])
    return f"tests/{module}/{page}"


def _has_explicit_test_target(args: List[str], *, root: Path) -> bool:
    """
    判断用户是否在 pytest 透传参数里显式指定了测试目标（目录/文件）。
    - 若未指定：默认只跑本次 URL 对应 suite 目录
    """
    for a in (args or []):
        s = (a or "").strip()
        if not s:
            continue
        if s.startswith("-"):
            continue
        if s.startswith("tests/") or s.startswith("tests\\"):
            return True
        if s.endswith(".py"):
            return True
        try:
            if (root / s).exists():
                return True
        except Exception:
            continue
    return False


def _pick_default_storage_state(root: Path) -> Optional[str]:
    """
    尽量复用已有登录态，避免分析阶段被重定向到登录页导致生成错误的 selectors。

    优先级：
    - .auth/storage_state.master.json
    - .auth/storage_state.*.json（按 mtime 最新）
    """
    auth_dir = root / ".auth"
    prefer = auth_dir / "storage_state.master.json"
    try:
        if prefer.exists() and prefer.stat().st_size > 0:
            return str(prefer)
    except Exception:
        pass

    try:
        cands = sorted(auth_dir.glob("storage_state.*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in cands:
            try:
                if p.exists() and p.stat().st_size > 0:
                    return str(p)
            except Exception:
                continue
    except Exception:
        pass
    return None


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--url", required=True, help="Target page URL. e.g. https://localhost:3000/admin/profile/change-password")
@click.option(
    "--analysis-json",
    default="",
    help="Optional PageInfo JSON path (usually exported from Cursor Playwright MCP). When set, skip Playwright analysis.",
)
@click.option("--storage-state", default="", help="Optional storage_state.json path for analysis (logged-in analysis).")
@click.option(
    "--artifacts-dir",
    default="reports/analysis",
    show_default=True,
    help="Directory to dump dynamic analysis artifacts (DOM/screenshot/a11y) for auditing.",
)
@click.option("--headless/--headed", default=True, help="Run browser headless during analysis.")
@click.option("--timeout-ms", default=60_000, show_default=True, type=int)
@click.option("--no-clean", is_flag=True, help="Do not clean artifacts before running pytest.")
@click.option("--no-run", is_flag=True, help="Only analyze+generate; do not run pytest.")
@click.option("--no-report", is_flag=True, help="Do not generate allure-report (still keeps allure-results if pytest runs).")
@click.option("--no-rules", is_flag=True, help="Do not load .cursor/rules into runtime context.")
@click.option(
    "--rules-out",
    default="reports/rules_context.md",
    show_default=True,
    help="Write merged rules context markdown to this path (relative to project root).",
)
@click.pass_context
def main(
    ctx: click.Context,
    *,
    url: str,
    analysis_json: str,
    storage_state: str,
    artifacts_dir: str,
    headless: bool,
    timeout_ms: int,
    no_clean: bool,
    no_run: bool,
    no_report: bool,
    no_rules: bool,
    rules_out: str,
) -> None:
    """
    官方入口：强制走“页面分析 + 全量生成”。

    - 默认必做：PageAnalyzer.analyze(url) → TestCodeGenerator.generate_all(...)
    - 然后（默认）：清理运行产物 → pytest → allure generate
    - 额外 pytest 参数：透传到命令末尾，例如：
        python3 -m tools.url_flow --url ... -- -m "P0 or P1" -n 4
    """
    root = _project_root()
    os.chdir(str(root))
    rules_cfg = get_rules_config(root=root)

    click.echo(f"root: {root}")
    click.echo(f"url: {url}")
    click.echo(f"analysis_artifacts: {artifacts_dir}")
    if analysis_json:
        click.echo(f"analysis_json: {analysis_json}")

    # 0) 规则上下文（可审计）：把 .cursor/rules 落成运行产物，确保“生成过程调用 rule”是可验证事实
    if (not no_rules) and rules_cfg.runtime_rules_context_enabled:
        out_path = (root / (rules_cfg.runtime_rules_context_output_path or rules_out or "")).resolve()
        rules_ctx = load_rules_context(root=root)
        write_rules_context(rules_ctx, out_path)
        os.environ["PT_RULES_CONTEXT_PATH"] = str(out_path)
        click.echo(f"rules: loaded={len(rules_ctx.sources)} → {out_path.relative_to(root)}")
    else:
        click.echo("rules: skipped")

    sp: Optional[str] = storage_state.strip() or None
    if sp is None and rules_cfg.default_storage_state_enabled:
        sp = _pick_default_storage_state(root)
        if sp:
            click.echo(f"storage_state(default): {Path(sp).relative_to(root)}")

    # 1) 分析（必选）
    # - 默认：Playwright 动态分析（可落盘 DOM/screenshot/a11y）
    # - 若提供 --analysis-json：直接读取 PageInfo（通常来自 Cursor Playwright MCP），跳过 Playwright
    if analysis_json.strip():
        p = Path(analysis_json).expanduser()
        if not p.exists():
            raise SystemExit(f"--analysis-json not found: {analysis_json}")
        raw = json.loads(p.read_text(encoding="utf-8", errors="ignore") or "{}")
        page_info = page_info_from_dict(raw if isinstance(raw, dict) else {})
        # 兜底：保证 url 不为空（生成器依赖 URL 推导命名）
        if not (page_info.url or "").strip():
            page_info.url = url
        # 审计：把输入快照复制到 artifacts-dir 方便回溯
        ad = (artifacts_dir or "").strip()
        if ad:
            out_dir = root / ad
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "incoming_analysis.json").write_text(
                json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    else:
        page_info = PageAnalyzer().analyze(
            url,
            storage_state_path=sp,
            artifacts_dir=artifacts_dir.strip() or None,
            headless=headless,
            timeout_ms=timeout_ms,
        )

    # 2) 全量生成（必选）
    TestCodeGenerator().generate_all(page_info, output_dir=".")
    click.echo("✅ generated: page objects + suites + test-data")

    if no_run:
        click.echo("ℹ️  --no-run set: skip pytest")
        return

    # 3) 清理（默认必做）
    if not no_clean:
        _clean_artifacts(root)
        click.echo("✅ cleaned: allure-results/allure-report/screenshots/reports/.pytest_cache")

    # 4) pytest（额外参数透传）
    extra_pytest_args = list(ctx.args or [])
    if rules_cfg.pytest_default_target_from_url_enabled and (not _has_explicit_test_target(extra_pytest_args, root=root)):
        suite_dir = _infer_suite_dir_from_url(url)
        extra_pytest_args = [suite_dir] + extra_pytest_args
        click.echo(f"pytest_target(default): {suite_dir}")
    cmd = [sys.executable, "-m", "pytest"] + extra_pytest_args
    _run(cmd, cwd=root, check=True)

    # 5) allure report（可选）
    if no_report:
        click.echo("ℹ️  --no-report set: skip allure generate")
        return

    allure = shutil.which("allure")
    if not allure:
        click.echo("⚠️  allure not found in PATH; skip allure-report generation.")
        return

    _run([allure, "generate", "-c", "allure-results", "-o", "allure-report"], cwd=root, check=True)
    click.echo("✅ allure-report generated: ./allure-report")
    click.echo("ℹ️  open via: python3 -m http.server 59717 --bind 127.0.0.1 --directory \"allure-report\"")


if __name__ == "__main__":
    main()


