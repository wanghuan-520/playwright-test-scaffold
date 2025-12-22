"""
# ═══════════════════════════════════════════════════════════════
# AI Command Router (natural language → full URL flow)
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 让你输入一句话就跑完整链路：
#     “测试下 https://...”
#     “测试下修改密码页面”
#   → 自动：分析 + 全量生成 + pytest + allure + 打开报告
#
# 实现策略：
# - 优先从输入中提取 URL
# - 否则从 `docs/requirements.md` 的“页面别名 → 路由”表中解析 alias → path
# - path 使用 config/project.yaml 中的 frontend base url 拼接成完整 URL
#
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils.config import ConfigManager


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _extract_url(text: str) -> Optional[str]:
    # 抓取第一个 http/https URL（只允许 RFC3986 常见字符，避免把“页面/中文标点”等误吞进 URL）
    # 例：`帮我测试下https://localhost:3000/admin/profile/change-password页面`
    # 旧实现会匹配到 `...change-password页面`（非法 URL）；这里会正确截断为 `...change-password`
    pattern = r"(https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)"
    m = re.search(pattern, text or "")
    if not m:
        return None
    return m.group(1).strip().rstrip(").,，。；;】】》》")


def _normalize_query(text: str) -> str:
    t = (text or "").strip()
    # 去掉常见引导词
    for k in ["帮我", "请", "麻烦", "测试下", "测试一下", "测试", "跑下", "跑一下", "页面", "用例"]:
        t = t.replace(k, "")
    return t.strip()

def _is_system_query(text: str) -> bool:
    """
    判断用户是否在表达“测试整个系统/跑回归”，而不是“测试某个页面”。
    """
    q = _normalize_query(text).lower()
    if not q:
        return False
    keywords = {
        "这个系统",
        "整个系统",
        "全系统",
        "全站",
        "全量",
        "回归",
        "regression",
        "smoke",
        "e2e",
    }
    return any(k in q for k in keywords)


def _split_alias_cell(s: str) -> List[str]:
    raw = (s or "").strip()
    if not raw:
        return []
    parts: List[str] = [raw]
    for sep in [",", "，", "、", ";", "；", "/"]:
        parts = [x for p in parts for x in p.split(sep)]
    return [x.strip().lower() for x in parts if x.strip()]


def _parse_alias_table(md_path: Path) -> Dict[str, str]:
    """
    解析 docs/requirements.md 中的 alias → path 表。

    规则：扫描形如
      | 别名 | /path | 说明 |
    的行，提取 alias cell + path cell。
    """
    if not md_path.exists():
        return {}
    lines = md_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    mapping: Dict[str, str] = {}
    for ln in lines:
        s = ln.strip()
        if not (s.startswith("|") and "|" in s):
            continue
        # 跳过表头分隔线
        if set(s.replace("|", "").strip()) <= {"-", " "}:
            continue
        cols = [c.strip() for c in s.strip("|").split("|")]
        if len(cols) < 2:
            continue
        alias_cell, path_cell = cols[0], cols[1]
        if not path_cell.startswith("/"):
            continue
        for a in _split_alias_cell(alias_cell):
            mapping[a] = path_cell
    return mapping


def _join_url(base: str, path: str) -> str:
    b = (base or "").rstrip("/")
    p = (path or "").strip()
    if not b:
        return p
    if not p.startswith("/"):
        p = "/" + p
    return f"{b}{p}"


def _find_free_port(prefer: int = 59717) -> int:
    # 先尝试固定端口，再兜底找一个空闲端口
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


def _run_url_flow(url: str, extra_pytest_args: List[str]) -> None:
    root = _project_root()
    cmd = [
        sys.executable,
        "-m",
        "tools.url_flow",
        "--url",
        url,
    ]
    if extra_pytest_args:
        cmd.append("--")
        cmd.extend(extra_pytest_args)
    print(f"\n$ {' '.join(shlex.quote(x) for x in cmd)}")
    p = subprocess.run(cmd, cwd=str(root))
    if p.returncode != 0:
        raise SystemExit(p.returncode)

def _run_pytest(extra_pytest_args: List[str]) -> None:
    """
    系统级回归：直接运行 pytest（不做页面分析/生成）。
    """
    root = _project_root()
    cmd = [sys.executable, "-m", "pytest"] + list(extra_pytest_args or [])
    print(f"\n$ {' '.join(shlex.quote(x) for x in cmd)}")
    p = subprocess.run(cmd, cwd=str(root))
    if p.returncode != 0:
        raise SystemExit(p.returncode)

def _try_generate_allure_report() -> None:
    """
    若本机安装了 allure，且存在 allure-results，则生成 allure-report。
    """
    root = _project_root()
    report_dir = root / "allure-report"
    results_dir = root / "allure-results"
    allure = shutil.which("allure")
    if not allure:
        return
    if not results_dir.exists():
        return
    cmd = [allure, "generate", "-c", str(results_dir), "-o", str(report_dir)]
    print(f"\n$ {' '.join(shlex.quote(x) for x in cmd)}")
    p = subprocess.run(cmd, cwd=str(root))
    if p.returncode != 0:
        print(f"⚠️  allure generate failed (exit={p.returncode})")


def _serve_allure_report(report_dir: Path, *, port: int) -> Tuple[int, str, int]:
    """
    后台启动 http.server，返回 (port, url, pid)。
    """
    root = _project_root()
    url = f"http://127.0.0.1:{port}/"
    cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(port),
        "--bind",
        "127.0.0.1",
        "--directory",
        str(report_dir),
    ]
    p = subprocess.Popen(cmd, cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 给 server 一点启动时间
    time.sleep(0.3)
    return port, url, int(p.pid)

def _split_argv_by_double_dash(argv: List[str]) -> Tuple[List[str], List[str]]:
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def _parse_router_opts(tokens: List[str]) -> Tuple[bool, int, List[str]]:
    """
    从 `--` 之前解析路由器自己的参数，其余都视为 query tokens。
    支持：
      --no-open
      --port <int>
      -h/--help
    """
    no_open = False
    port = 59717
    query_tokens: List[str] = []

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in {"-h", "--help"}:
            print(
                "Usage:\n"
                "  python3 -m tools.ai_command_router 测试下 修改密码页面\n"
                "  python3 -m tools.ai_command_router 测试下 https://localhost:3000/admin/profile/change-password\n"
                "  python3 -m tools.ai_command_router 测试下 修改密码页面 -- -m \"P0 or P1\" -n 4\n"
                "\nOptions:\n"
                "  --no-open        Do not open browser automatically\n"
                "  --port <int>     Preferred port for http.server (default 59717)\n"
            )
            raise SystemExit(0)
        if t == "--no-open":
            no_open = True
            i += 1
            continue
        if t == "--port":
            if i + 1 >= len(tokens):
                raise SystemExit("--port requires an int value")
            port = int(tokens[i + 1])
            i += 2
            continue
        # 非选项 → query
        query_tokens.append(t)
        i += 1

    return no_open, port, query_tokens


def main() -> None:
    """
    设计目标：支持“不加引号”的自然语言输入，并且支持 `--` 之后透传 pytest 参数。
    """
    root = _project_root()
    os.chdir(str(root))

    left, extra_pytest_args = _split_argv_by_double_dash(sys.argv[1:])
    no_open, port, query_tokens = _parse_router_opts(left)

    raw = " ".join(query_tokens).strip()
    if not raw:
        raise SystemExit("missing query. Use: python3 -m tools.ai_command_router 测试下 修改密码页面")

    # 0) “测试整个系统/跑回归”优先：不需要 URL / alias
    if _is_system_query(raw):
        print("mode: system")
        _run_pytest(extra_pytest_args)
        _try_generate_allure_report()
    else:
        # 1) URL 优先
        url = _extract_url(raw)

        # 2) alias → path → url
        if not url:
            q = _normalize_query(raw).lower()
            mapping = _parse_alias_table(root / "docs" / "requirements.md")
            path = mapping.get(q)
            if not path:
                # 宽松匹配：包含关系（避免用户输入“修改密码”而不是“修改密码页面”）
                for k, v in mapping.items():
                    if k and (k in q or q in k):
                        path = v
                        break
            if not path:
                raise SystemExit(
                    f"无法从输入解析 URL，也无法命中页面别名映射：{raw}\n"
                    f"请在 docs/requirements.md 的“页面别名 → 路由”表中新增别名，或直接输入 URL。"
                )

            cfg = ConfigManager()
            base = (cfg.get_service_url("frontend") or "").rstrip("/")
            url = _join_url(base, path)

        print(f"url_resolved: {url}")
        _run_url_flow(url, extra_pytest_args)

    # 3) 启动并打开 Allure report
    report_dir = root / "allure-report"
    if not report_dir.exists():
        # url_flow 可能用了 --no-report，或者这是系统回归且之前没生成；这里兜底尝试生成一次
        _try_generate_allure_report()
    if not report_dir.exists():
        print("⚠️  allure-report not found (maybe allure not installed). Skip auto-open.")
        return

    real_port = _find_free_port(prefer=int(port))
    _, report_url, pid = _serve_allure_report(report_dir, port=real_port)
    print(f"✅ allure report server: pid={pid} url={report_url}")
    if not no_open:
        try:
            webbrowser.open(report_url, new=2)
        except Exception:
            pass


if __name__ == "__main__":
    main()


