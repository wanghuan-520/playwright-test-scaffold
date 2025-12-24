"""
# ═══════════════════════════════════════════════════════════════
# Allure Suite Cache - Latest-per-suite + Combined Report
# ═══════════════════════════════════════════════════════════════
#
# 需求：
# - 同一 suite 多次运行：报告里只保留该 suite 的“最新一次结果”
# - 不同 suite 分开运行：最终报告展示“各 suite 的最新结果合集”
#
# 约束：
# - 不改名附件文件：Allure 的 json 通过 `source` 引用附件名，改名会断链
# - 不引入第三方依赖
#
# 方案：
# - 每个 suite 单独缓存 results：`.allure-cache/<suite_key>/allure-results`
# - 每次 pytest 运行完成后，把 `allure-results/` 覆盖同步到对应 suite 的缓存目录
# - 生成报告时：用 Allure CLI 的“多 results 目录输入”能力，把所有 suite 的最新 results 一次性生成到 `allure-report/`
#
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cache_root() -> Path:
    return project_root() / ".allure-cache"


def sanitize_suite_key(s: str) -> str:
    raw = (s or "").strip().lower()
    if not raw:
        return "default"
    out = []
    for ch in raw:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    key = "".join(out)
    while "__" in key:
        key = key.replace("__", "_")
    return key.strip("_") or "default"


def suite_results_dir(suite_key: str) -> Path:
    k = sanitize_suite_key(suite_key)
    return cache_root() / k / "allure-results"


def list_cached_suites() -> List[str]:
    root = cache_root()
    if not root.exists():
        return []
    suites: List[str] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if (p / "allure-results").exists():
            suites.append(p.name)
    suites.sort()
    return suites


def _reset_dir(p: Path) -> None:
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True, exist_ok=True)


def sync_suite_results(*, suite_key: str, src_results_dir: Path) -> Path:
    """
    覆盖写入某个 suite 的最新 results。
    """
    src = src_results_dir
    if not src.exists() or not src.is_dir():
        raise RuntimeError(f"src_results_dir not found: {src}")

    dst = suite_results_dir(suite_key)
    _reset_dir(dst)

    # copytree 目标需不存在；我们已 reset_dir，所以逐文件复制
    for p in src.iterdir():
        if p.is_dir():
            continue
        shutil.copy2(p, dst / p.name)
    return dst


def _allure_binary() -> Optional[str]:
    return shutil.which("allure")


def generate_report(*, report_dir: Path, include_suites: Optional[Iterable[str]] = None) -> int:
    """
    从所有 suite 的最新 results 生成一个“完整最新”的报告。
    """
    allure = _allure_binary()
    if not allure:
        print("allure not found in PATH", file=sys.stderr)
        return 2

    suites = list_cached_suites()
    if include_suites is not None:
        want = {sanitize_suite_key(x) for x in include_suites}
        suites = [s for s in suites if sanitize_suite_key(s) in want]

    # 允许“第一次运行还没有 cache”：fallback 到项目根的 allure-results
    results_dirs: List[str] = []
    for s in suites:
        d = cache_root() / sanitize_suite_key(s) / "allure-results"
        if d.exists():
            results_dirs.append(str(d))
    if not results_dirs:
        fallback = project_root() / "allure-results"
        if fallback.exists():
            results_dirs = [str(fallback)]

    if not results_dirs:
        print("no allure results found (cache empty and allure-results missing)", file=sys.stderr)
        return 2

    # clear report dir and generate
    _reset_dir(report_dir)
    cmd = [allure, "generate", "-c", *results_dirs, "-o", str(report_dir)]
    print(f"\n$ {' '.join(cmd)}")
    try:
        p = subprocess.run(cmd, cwd=str(project_root()))
        return int(p.returncode)
    except BlockingIOError as e:
        # 某些环境在进程资源紧张时会 fork 失败（例如 "Resource temporarily unavailable"）
        print(f"failed to spawn allure: {type(e).__name__}: {e}", file=sys.stderr)
        print("You can retry later or run the command manually:", file=sys.stderr)
        print(f"  {' '.join(cmd)}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"failed to spawn allure: {type(e).__name__}: {e}", file=sys.stderr)
        print("You can retry later or run the command manually:", file=sys.stderr)
        print(f"  {' '.join(cmd)}", file=sys.stderr)
        return 2


def _guess_suite_key(guess_from: str) -> str:
    g = (guess_from or "").strip()
    if not g:
        return "default"
    return sanitize_suite_key(g)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="allure_cache")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="sync current allure-results into suite cache")
    p_sync.add_argument("--suite-key", default="", help="suite key (default: guessed)")
    p_sync.add_argument("--guess-from", default="", help="guess key from TEST_TARGET/label")
    p_sync.add_argument("--src", default="allure-results", help="source allure-results directory")

    p_report = sub.add_parser("report", help="generate combined report from cached suites")
    p_report.add_argument("--out", default="allure-report", help="output report directory")
    p_report.add_argument("--include", default="", help="comma-separated suite keys to include (optional)")

    p_list = sub.add_parser("list", help="list cached suites")

    args = parser.parse_args(argv)

    if args.cmd == "sync":
        suite_key = (args.suite_key or "").strip() or _guess_suite_key(args.guess_from)
        src = project_root() / str(args.src)
        dst = sync_suite_results(suite_key=suite_key, src_results_dir=src)
        print(f"synced suite={sanitize_suite_key(suite_key)} -> {dst}")
        return 0

    if args.cmd == "report":
        include = [x.strip() for x in (args.include or "").split(",") if x.strip()]
        rc = generate_report(report_dir=project_root() / str(args.out), include_suites=include or None)
        return rc

    if args.cmd == "list":
        for s in list_cached_suites():
            print(s)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())


