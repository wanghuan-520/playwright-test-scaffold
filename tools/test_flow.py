"""
# ═══════════════════════════════════════════════════════════════
# Test Flow Runner (suite-aware, merged latest report)
# ═══════════════════════════════════════════════════════════════
#
# 解决的问题：
# - 同一目录反复跑：只保留“最后一次”的结果
# - 不同目录分开跑：报告展示“各目录最后一次”的合并结果
#
# 使用方式：
#   python3 -m tools.test_flow --suite profile -- tests/admin/profile
#   python3 -m tools.test_flow --suite profile -- tests/admin/profile
#   python3 -m tools.test_flow --suite profile_change_password -- tests/admin/profile_change_password
#
# 透传 pytest 参数：
#   python3 -m tools.test_flow --suite profile -- -m "P0 or P1" -n 4 tests/admin/profile
#
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple, Optional

from tools.allure_manager import (
    generate_allure_report,
    rebuild_combined_results,
    run_pytest_to_suite_results,
    serve_report_and_open,
)


def _split_argv_by_double_dash(argv: List[str]) -> Tuple[List[str], List[str]]:
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def _infer_suite_from_pytest_args(pytest_args: List[str]) -> str:
    """
    从 pytest 参数中推断 suite key，尽量让 `tools.test_flow` 在“按目录跑用例”时零配置可用。

    规则（从后往前找第一个“像测试路径”的参数）：
    - tests/admin/profile_change_password  -> profile_change_password
    - tests/admin/profile                 -> profile
    - tests/test_example.py               -> test_example
    - 若无法推断，返回 default
    """
    for t in reversed(pytest_args or []):
        s = (t or "").strip()
        if not s:
            continue
        if s.startswith("-"):
            continue
        # 只要包含 tests/，基本就是测试目标路径
        if "tests/" in s or s.startswith("tests"):
            p = s.rstrip("/").split("/")[-1]
            if p.endswith(".py"):
                p = p[:-3]
            return p or "default"
    return "default"


def _parse_args(argv: List[str]) -> Tuple[Optional[str], bool, int, bool]:
    suite: Optional[str] = None
    no_open = False
    port = 59717
    no_serve = False

    i = 0
    while i < len(argv):
        t = argv[i]
        if t in {"-h", "--help"}:
            print(
                "Usage:\n"
                "  python3 -m tools.test_flow [--suite <suite_key>] -- <pytest_args>\n"
                "\nExamples:\n"
                "  python3 -m tools.test_flow --suite profile -- tests/admin/profile\n"
                "  python3 -m tools.test_flow -- tests/admin/profile\n"
                "  python3 -m tools.test_flow -- tests/admin/profile_change_password\n"
                "\nOptions:\n"
                "  --suite <key>    Optional. Cache key (overwrites previous run of same suite). If omitted, inferred from pytest target path.\n"
                "  --no-open        Do not open browser automatically\n"
                "  --port <int>     Preferred port for http.server (default 59717)\n"
                "  --no-serve       Do not start http.server (only generate allure-report)\n"
            )
            raise SystemExit(0)
        if t == "--suite":
            if i + 1 >= len(argv):
                raise SystemExit("--suite requires a value")
            suite = argv[i + 1].strip() or None
            i += 2
            continue
        if t == "--no-open":
            no_open = True
            i += 1
            continue
        if t == "--no-serve":
            no_serve = True
            i += 1
            continue
        if t == "--port":
            if i + 1 >= len(argv):
                raise SystemExit("--port requires an int value")
            port = int(argv[i + 1])
            i += 2
            continue
        raise SystemExit(f"unknown arg before '--': {t} (use --help)")

    return suite, no_open, port, no_serve


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    left, pytest_args = _split_argv_by_double_dash(sys.argv[1:])
    suite_opt, no_open, port, no_serve = _parse_args(left)
    if not pytest_args:
        raise SystemExit("missing pytest args after '--'. Example: -- tests/admin/profile")

    suite = suite_opt or _infer_suite_from_pytest_args(pytest_args)

    # 1) 跑该 suite：写入独立 results（覆盖旧）
    rc = run_pytest_to_suite_results(pytest_args, suite_key=suite)
    if rc != 0:
        raise SystemExit(rc)

    # 2) 合并所有 suite 的最新结果 → combined allure-results
    rebuild_combined_results()

    # 3) 生成报告
    ok, reason = generate_allure_report()
    if not ok:
        raise SystemExit(f"allure generate failed: {reason}")

    # 4) 打开报告（后台 server）
    if no_serve:
        print("✅ allure-report generated: ./allure-report (no server started)")
        return
    p, url, pid = serve_report_and_open(port=port, no_open=no_open)
    print(f"✅ allure report server: pid={pid} url={url} (port={p})")


if __name__ == "__main__":
    main()


