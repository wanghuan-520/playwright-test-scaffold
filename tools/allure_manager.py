"""
# ═══════════════════════════════════════════════════════════════
# Allure Results Manager (suite cache + combined report)
# ═══════════════════════════════════════════════════════════════
#
# 需求（来自用户真实使用场景）：
# - 同一个 suite 多次运行：只保留该 suite 的“最新结果”
# - 不同 suite 分开运行：最终报告展示“各 suite 的最新结果合集”
#
# 方案：
# - 每个 suite 单独保存 results：`.allure-cache/<suite_key>/allure-results`
# - 每次运行前清空该 suite 的 results 目录（覆盖为最新）
# - 生成报告前重建 combined results：`allure-results/` 由所有 suite results 合并而来
# - 文件名冲突兜底：copy 时加前缀 `<suite_key>__`
#
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


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
    # 压缩连续下划线
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
    suites = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if (p / "allure-results").exists():
            suites.append(p.name)
    suites.sort()
    return suites


def reset_dir(p: Path) -> None:
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True, exist_ok=True)


def run_pytest_to_suite_results(pytest_args: List[str], *, suite_key: str) -> int:
    """
    运行 pytest，将结果写入该 suite 的 results 目录（覆盖旧结果）。
    """
    root = project_root()
    out_dir = suite_results_dir(suite_key)
    reset_dir(out_dir)

    cmd = [sys.executable, "-m", "pytest", f"--alluredir={str(out_dir)}"] + list(pytest_args or [])
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(root))
    return int(p.returncode)


def rebuild_combined_results(include_suites: Optional[Iterable[str]] = None) -> Path:
    """
    合并所有 suite 的最新结果到项目根 `allure-results/`。
    """
    root = project_root()
    combined = root / "allure-results"
    reset_dir(combined)

    suites = list_cached_suites()
    if include_suites is not None:
        want = {sanitize_suite_key(x) for x in include_suites}
        suites = [s for s in suites if sanitize_suite_key(s) in want]

    for s in suites:
        src = suite_results_dir(s)
        if not src.exists():
            continue
        for f in src.iterdir():
            if not f.is_file():
                continue
            # 关键：不要改名！
            # Allure 的 result/container json 里通过 `source` 字段引用附件文件名；
            # 若合并时给文件加前缀，会导致报告里“点击截图没反应”（附件 404）。
            #
            # 理论上不同 suite 的附件名（uuid）冲突概率极低；即使极端冲突，覆盖也比断链更可接受。
            dst = combined / f.name
            shutil.copy2(str(f), str(dst))
    return combined


def generate_allure_report() -> Tuple[bool, str]:
    """
    使用 combined results 生成 allure-report/。
    """
    root = project_root()
    allure = shutil.which("allure")
    if not allure:
        return False, "allure_not_found"

    cmd = [allure, "generate", "-c", "allure-results", "-o", "allure-report"]
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(root))
    return (p.returncode == 0), f"exit={p.returncode}"


def _find_free_port(prefer: int = 59717) -> int:
    for port in [prefer] + list(range(prefer + 1, prefer + 20)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def serve_report_and_open(*, port: int = 59717, no_open: bool = False) -> Tuple[int, str, int]:
    """
    后台启动 http.server 打开 allure-report/，返回 (port, url, pid)。
    """
    root = project_root()
    report_dir = root / "allure-report"
    if not report_dir.exists():
        raise RuntimeError("allure-report not found")

    real_port = _find_free_port(prefer=int(port))
    url = f"http://127.0.0.1:{real_port}/"
    cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(real_port),
        "--bind",
        "127.0.0.1",
        "--directory",
        str(report_dir),
    ]
    p = subprocess.Popen(cmd, cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.3)
    if not no_open:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass
    return real_port, url, int(p.pid)


