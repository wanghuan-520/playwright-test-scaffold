#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试产生的多余角色

用法：
    python scripts/cleanup_test_roles.py

功能：
    1. 连接后端 API 获取所有角色
    2. 保留系统角色（admin, member 等 static 角色）
    3. 删除测试产生的角色（名称包含 TestRole_, test_, auto_ 等）
"""

import sys
import os
import requests
from typing import List, Dict, Any

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.config_manager import ConfigManager

logger = get_logger(__name__)

# 系统保留角色（不会被删除）
RESERVED_ROLES = {"admin", "member"}

# 测试角色名称模式（匹配这些模式的角色会被删除）
TEST_ROLE_PATTERNS = [
    "testrole",
    "test_role",
    "test-role",
    "auto_role",
    "autorole",
    "temp_role",
    "temprole",
    "_test",
    "role_test",
    "role-test",
]


def is_test_role(role_name: str) -> bool:
    """
    判断是否是测试角色
    
    Args:
        role_name: 角色名称
        
    Returns:
        bool: 是否是测试角色
    """
    name_lower = role_name.lower()
    
    # 检查是否是系统保留角色
    if name_lower in RESERVED_ROLES:
        return False
    
    # 检查是否匹配测试角色模式
    for pattern in TEST_ROLE_PATTERNS:
        if pattern in name_lower:
            return True
    
    return False


def get_all_roles(backend_url: str, session: requests.Session) -> List[Dict[str, Any]]:
    """
    获取所有角色
    
    Args:
        backend_url: 后端 URL
        session: requests Session
        
    Returns:
        角色列表
    """
    try:
        response = session.get(
            f"{backend_url}/api/identity/roles",
            params={"MaxResultCount": 1000},
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return []


def delete_role(backend_url: str, session: requests.Session, role_id: str, role_name: str) -> bool:
    """
    删除角色
    
    Args:
        backend_url: 后端 URL
        session: requests Session
        role_id: 角色 ID
        role_name: 角色名称
        
    Returns:
        bool: 是否删除成功
    """
    try:
        response = session.delete(
            f"{backend_url}/api/identity/roles/{role_id}",
            headers={"Accept": "application/json"}
        )
        if response.status_code in [200, 204]:
            logger.info(f"✓ 已删除角色: {role_name} (ID: {role_id})")
            return True
        else:
            logger.warning(f"✗ 删除角色失败: {role_name}, 状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ 删除角色时出错: {role_name}, 错误: {e}")
        return False


def login_and_get_session(backend_url: str, username: str, password: str) -> requests.Session:
    """
    登录并获取 session
    
    Args:
        backend_url: 后端 URL
        username: 用户名
        password: 密码
        
    Returns:
        requests.Session: 已认证的 session
    """
    session = requests.Session()
    
    try:
        # ABP 登录
        response = session.post(
            f"{backend_url}/api/account/login",
            json={"userNameOrEmailAddress": username, "password": password},
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info(f"登录成功: {username}")
            return session
        else:
            logger.warning(f"登录失败，状态码: {response.status_code}")
            # 继续尝试，可能不需要登录（开发环境）
            return session
    except Exception as e:
        logger.warning(f"登录时出错: {e}，继续尝试...")
        return session


def cleanup_test_roles(
    backend_url: str = None,
    username: str = "admin",
    password: str = "1q2w3E*",
    dry_run: bool = False,
    delete_all_non_system: bool = False
) -> Dict[str, Any]:
    """
    清理测试角色
    
    Args:
        backend_url: 后端 URL（默认从配置读取）
        username: 管理员用户名
        password: 管理员密码
        dry_run: 只预览，不实际删除
        delete_all_non_system: 是否删除所有非系统角色
        
    Returns:
        dict: 清理结果
    """
    # 获取后端 URL
    if not backend_url:
        try:
            config = ConfigManager()
            backend_url = config.get_service_url("backend") or "http://localhost:5678"
        except Exception:
            backend_url = "http://localhost:5678"
    
    logger.info(f"后端 URL: {backend_url}")
    logger.info(f"模式: {'预览模式' if dry_run else '执行模式'}")
    logger.info(f"删除范围: {'所有非系统角色' if delete_all_non_system else '仅测试角色'}")
    logger.info("-" * 50)
    
    # 登录
    session = login_and_get_session(backend_url, username, password)
    
    # 获取所有角色
    roles = get_all_roles(backend_url, session)
    logger.info(f"获取到 {len(roles)} 个角色")
    
    if not roles:
        return {"total": 0, "deleted": 0, "skipped": 0, "failed": 0}
    
    # 分类角色
    roles_to_delete = []
    roles_to_keep = []
    
    for role in roles:
        role_name = role.get("name", "")
        is_static = role.get("isStatic", False)
        
        # 系统角色（static）不删除
        if is_static:
            roles_to_keep.append(role_name)
            continue
        
        # 保留角色不删除
        if role_name.lower() in RESERVED_ROLES:
            roles_to_keep.append(role_name)
            continue
        
        # 判断是否需要删除
        if delete_all_non_system or is_test_role(role_name):
            roles_to_delete.append(role)
        else:
            roles_to_keep.append(role_name)
    
    logger.info(f"保留角色 ({len(roles_to_keep)}): {', '.join(roles_to_keep)}")
    logger.info(f"待删除角色 ({len(roles_to_delete)}): {', '.join([r.get('name', '') for r in roles_to_delete])}")
    logger.info("-" * 50)
    
    if dry_run:
        logger.info("预览模式，不执行实际删除")
        return {
            "total": len(roles),
            "to_delete": len(roles_to_delete),
            "to_keep": len(roles_to_keep),
            "deleted": 0,
            "failed": 0,
            "roles_to_delete": [r.get("name") for r in roles_to_delete]
        }
    
    # 执行删除
    deleted_count = 0
    failed_count = 0
    
    for role in roles_to_delete:
        role_id = role.get("id")
        role_name = role.get("name", "")
        
        if delete_role(backend_url, session, role_id, role_name):
            deleted_count += 1
        else:
            failed_count += 1
    
    logger.info("-" * 50)
    logger.info(f"清理完成：删除 {deleted_count} 个，失败 {failed_count} 个，保留 {len(roles_to_keep)} 个")
    
    return {
        "total": len(roles),
        "deleted": deleted_count,
        "failed": failed_count,
        "kept": len(roles_to_keep)
    }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="清理测试产生的多余角色")
    parser.add_argument("--backend-url", "-b", help="后端 URL（默认: http://localhost:5678）")
    parser.add_argument("--username", "-u", default="admin", help="管理员用户名（默认: admin）")
    parser.add_argument("--password", "-p", default="1q2w3E*", help="管理员密码（默认: 1q2w3E*）")
    parser.add_argument("--dry-run", "-d", action="store_true", help="预览模式，不实际删除")
    parser.add_argument("--all", "-a", action="store_true", help="删除所有非系统角色（不仅仅是测试角色）")
    
    args = parser.parse_args()
    
    result = cleanup_test_roles(
        backend_url=args.backend_url,
        username=args.username,
        password=args.password,
        dry_run=args.dry_run,
        delete_all_non_system=args.all
    )
    
    print("\n" + "=" * 50)
    print("清理结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
