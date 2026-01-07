# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Root Conftest (Shared Session)
# ═══════════════════════════════════════════════════════════════

import sys
import time
from pathlib import Path
from typing import Dict

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入核心fixtures
from core.fixtures import *


# ═══════════════════════════════════════════════════════════════
# Pytest: 每个脚本(测试文件)运行时长统计
# ───────────────────────────────────────────────────────────────
# 目标：
# - 测试全部跑完后，按“测试文件”维度打印总耗时
# - 兼容 xdist：master 侧能收到各 worker 的 test report
# - 不侵入业务 fixture，单文件小插件即可
# ═══════════════════════════════════════════════════════════════

_FILE_DURATIONS_SEC: Dict[str, float] = {}


def _nodeid_to_file_key(nodeid: str) -> str:
    # nodeid 形如：tests/foo/test_bar.py::test_xxx[param]
    # 取 '::' 前面的部分作为“脚本”标识
    return nodeid.split("::", 1)[0]


def pytest_runtest_logreport(report):
    # 只在 call 阶段累加（setup/teardown 也可算，但通常用户关心 test body）
    if report.when != "call":
        return

    file_key = _nodeid_to_file_key(report.nodeid)
    _FILE_DURATIONS_SEC[file_key] = _FILE_DURATIONS_SEC.get(file_key, 0.0) + float(
        getattr(report, "duration", 0.0)
    )


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _FILE_DURATIONS_SEC:
        return

    terminalreporter.section("Per-script duration (grouped by test file)")

    items = sorted(_FILE_DURATIONS_SEC.items(), key=lambda kv: kv[1], reverse=True)
    for file_key, seconds in items:
        terminalreporter.write_line(f"{seconds:8.2f}s  {file_key}")
