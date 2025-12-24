"""
# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Pytest Fixtures (Facade)
# ═══════════════════════════════════════════════════════════════
#
# 说明：
# - 对外 import path 仍然是 `core.fixtures`（兼容 conftest.py 的 `from core.fixtures import *`）
# - 内部实现按职责拆分在 `core/fixture/*.py`，避免单文件过大导致维护困难
#
"""

# re-export (pytest fixtures / hooks)
from core.fixture.browser import *  # noqa: F403
from core.fixture.basic_pages import *  # noqa: F403
from core.fixture.urls_and_data import *  # noqa: F403
from core.fixture.service_env import *  # noqa: F403
from core.fixture.auth import *  # noqa: F403
from core.fixture.artifacts_and_accounts import *  # noqa: F403


