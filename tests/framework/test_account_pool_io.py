# ═══════════════════════════════════════════════════════════════
# Account Pool IO Unit Tests
# ═══════════════════════════════════════════════════════════════
"""account_pool_io 单元测试"""

import json
from pathlib import Path
from unittest.mock import MagicMock

from utils.account_pool_io import save_account_pool


def test_save_account_pool_supports_root_level_file(tmp_path, monkeypatch):
    """根目录文件路径应可正常保存（无子目录）。"""
    monkeypatch.chdir(tmp_path)
    logger = MagicMock()
    data = {
        "test_account_pool": [
            {"username": "u1", "password": "p1", "in_use": False, "is_locked": False}
        ],
        "pool_config": {},
    }

    save_account_pool("root_pool.json", data, logger)

    saved_file = Path("root_pool.json")
    assert saved_file.exists()
    saved = json.loads(saved_file.read_text(encoding="utf-8"))
    assert saved["test_account_pool"][0]["username"] == "u1"
