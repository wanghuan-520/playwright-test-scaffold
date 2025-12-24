"""
# ═══════════════════════════════════════════════════════════════
# Fixtures - Basic pages (non-auth)
# ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from core.fixture.shared import logger


@pytest.fixture(scope="function")
def test_page(page: Page) -> Page:
    """测试页面 fixture - 每个测试独立的页面实例"""
    logger.info("创建测试页面")
    yield page
    logger.info("关闭测试页面")


@pytest.fixture(scope="class")
def shared_page(browser) -> Page:
    """共享页面 fixture - 测试类内共享"""
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, ignore_https_errors=True)
    page = context.new_page()
    logger.info("创建共享页面")
    yield page
    logger.info("关闭共享页面")
    context.close()


