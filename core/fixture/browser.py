"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Browser configuration
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import pytest

from core.fixture.shared import config


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """配置浏览器上下文参数"""
    browser_config = config.get_browser_config()
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {
            "width": browser_config.get("viewport_width", 1920),
            "height": browser_config.get("viewport_height", 1080),
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
        "args": args
        if args
        else [
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--allow-insecure-localhost",
            "--disable-gpu",
            "--no-sandbox",
        ],
    }


