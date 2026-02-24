"""
账号池文件 I/O（纯函数）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def load_account_pool(account_pool_path: str, logger) -> Dict[str, Any]:
    """加载账号池数据。"""
    try:
        with open(account_pool_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "test_account_pool" not in data:
                logger.warning("账号池文件格式异常，缺少 test_account_pool 字段")
                return {"test_account_pool": [], "pool_config": {}}
            return data
    except FileNotFoundError:
        logger.error(f"账号池文件不存在: {account_pool_path}")
        return {"test_account_pool": [], "pool_config": {}}
    except json.JSONDecodeError as e:
        logger.error(f"账号池文件 JSON 格式错误: {e}")
        return {"test_account_pool": [], "pool_config": {}}
    except Exception as e:
        logger.error(f"加载账号池失败: {e}")
        return {"test_account_pool": [], "pool_config": {}}


def save_account_pool(account_pool_path: str, data: Dict[str, Any], logger) -> None:
    """保存账号池数据（原子替换）。"""
    if "test_account_pool" not in data:
        logger.error("保存失败：数据缺少 test_account_pool 字段")
        return

    pool = data.get("test_account_pool", [])
    if len(pool) == 0:
        logger.warning("警告：尝试保存空账号池，已跳过")
        return

    backup_path = f"{account_pool_path}.backup"
    if os.path.exists(account_pool_path):
        import shutil

        try:
            shutil.copy2(account_pool_path, backup_path)
        except Exception as e:
            logger.warning(f"创建备份失败: {e}")

    try:
        os.makedirs(os.path.dirname(account_pool_path), exist_ok=True)
        import time

        temp_file = f"{account_pool_path}.tmp.{os.getpid()}.{int(time.time() * 1000000)}"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with open(temp_file, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        if len(test_data.get("test_account_pool", [])) == 0:
            logger.warning("警告：临时文件账号池为空，不替换原文件")
            os.remove(temp_file)
            return

        os.replace(temp_file, account_pool_path)
        logger.debug(f"账号池数据已保存（{len(pool)} 个账号）")
    except Exception as e:
        logger.error(f"保存账号池失败: {e}")
        try:
            for p in Path(os.path.dirname(account_pool_path)).glob(f"{Path(account_pool_path).name}.tmp.*"):
                p.unlink(missing_ok=True)
        except Exception:
            pass
        raise
