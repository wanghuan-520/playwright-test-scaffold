"""
Playwright runtime smoke tests.

目标：
- 验证 CI 环境中的浏览器安装与基础页面交互能力
- 不依赖业务服务地址，避免外部环境导致假失败
"""

import pytest
from playwright.sync_api import Page


@pytest.mark.smoke
@pytest.mark.e2e
def test_playwright_runtime_data_url(page: Page):
    """使用 data URL 做最小可执行烟测。"""
    html = """
    <html>
      <body>
        <h1 id="title">Playwright Smoke</h1>
        <button id="run">Run</button>
        <script>
          document.getElementById('run').addEventListener('click', function () {
            document.getElementById('title').textContent = 'Playwright Smoke OK';
          });
        </script>
      </body>
    </html>
    """

    page.goto(f"data:text/html,{html}", wait_until="domcontentloaded")
    page.click("#run")
    assert page.text_content("#title") == "Playwright Smoke OK"
