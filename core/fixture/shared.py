"""
# ═══════════════════════════════════════════════════════════════
# Fixtures Shared - Singletons & shared helpers
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 避免每个 module 各自 get_logger() 造成多份 handler（日志重复/文件句柄膨胀）
# - 统一提供 config/data_manager/logger 与少量通用 helper
#
"""

from __future__ import annotations

import socket
from urllib.parse import urlparse

from utils.config import ConfigManager
from utils.data_manager import DataManager
from utils.logger import get_logger

# 关键：固定 logger 名称，保证全套 fixtures 共享同一组 handler
logger = get_logger("core.fixtures")
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


def _is_tcp_open(url: str, *, timeout_s: float = 1.5) -> tuple[bool, str]:
    """
    最小网络可达性探针（fail-fast 用）：
    - 仅检查 host:port 是否可连接，不做 HTTP 请求（避免证书/代理/路径差异干扰）
    """
    try:
        u = (url or "").strip()
        if not u:
            return False, "empty_url"
        p = urlparse(u)
        host = p.hostname or ""
        if not host:
            return False, "missing_host"
        if p.port:
            port = int(p.port)
        else:
            port = 443 if (p.scheme or "").lower() == "https" else 80
        with socket.create_connection((host, port), timeout=timeout_s):
            return True, "ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


