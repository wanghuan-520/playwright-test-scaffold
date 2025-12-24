"""
# ═══════════════════════════════════════════════════════════════
# Service Checker - Minimal Health Checks (optional)
# ═══════════════════════════════════════════════════════════════
#
# 说明：
# - 该模块只用于“可选”的服务健康检查 fixture：core/fixtures.py:service_checker
# - 默认主流程是手动 pytest + allure；健康检查不应成为强依赖
#
# 设计：
# - 不引入第三方依赖（requests）
# - 以 config/project.yaml 的 health_check 配置为准
# - HTTPS 本地自签证书：默认跳过证书校验（避免 dev 环境阻塞）
#
"""

from __future__ import annotations

import ssl
import time
import urllib.request
from typing import Dict, Tuple

from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ServiceChecker:
    """
    服务健康检查器（可选）。
    """

    def __init__(self) -> None:
        self.config = ConfigManager()
        self.hc = self.config.get_health_check_config()

    def is_enabled(self) -> bool:
        return bool(self.hc.get("enabled", True))

    def _http_get_ok(self, url: str, *, timeout_s: float) -> Tuple[bool, str]:
        if not url:
            return False, "empty_url"
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout_s, context=ctx) as resp:  # noqa: S310
                code = int(getattr(resp, "status", 0) or 0)
                return (200 <= code < 500), f"status={code}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    def check_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """
        返回：{service_name: (ok, reason)}
        """
        timeout_s = float(self.hc.get("timeout", 10) or 10)
        retry_count = int(self.hc.get("retry_count", 3) or 3)
        retry_interval = float(self.hc.get("retry_interval", 2) or 2)

        services = self.config.get_all_services()
        results: Dict[str, Tuple[bool, str]] = {}

        for name in services.keys():
            url = self.config.get_health_check_url(name)
            ok = False
            reason = "unknown"
            for i in range(max(retry_count, 1)):
                ok, reason = self._http_get_ok(url, timeout_s=timeout_s)
                if ok:
                    break
                if i < retry_count - 1:
                    try:
                        time.sleep(retry_interval)
                    except Exception:
                        pass
            results[name] = (ok, reason)
        return results

    def get_status_report(self) -> str:
        """
        打印友好报告（用于 pytest 运行时输出）。
        """
        services = self.config.get_all_services()
        lines = ["", "Service Health Check", "-------------------"]
        for name, cfg in services.items():
            lines.append(f"- {name}: {cfg.get('url', '')}{cfg.get('health_check', '')}")
        return "\n".join(lines) + "\n"


