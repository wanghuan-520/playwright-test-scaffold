#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量删除角色脚本（排除 admin 和 member）

功能：
- 获取所有角色列表
- 过滤掉系统角色（admin、member）
- 批量删除其他角色

使用方法：
    python3 scripts/cleanup_roles.py

环境变量：
    BACKEND_URL: 后端 API 地址（默认: http://localhost:5678）
    ADMIN_USERNAME: Admin 用户名（默认: admin）
    ADMIN_PASSWORD: Admin 密码（默认: 1q2w3E*）
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional

# 默认配置
DEFAULT_BACKEND_URL = "http://localhost:5678"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "1q2w3E*"

# 系统角色（不删除）
SYSTEM_ROLES = {"admin", "member"}


def get_auth_session(backend_url: str, username: str, password: str) -> Optional[requests.Session]:
    """
    获取认证 Session（使用 Cookie 认证）
    
    Args:
        backend_url: 后端 API 地址
        username: 用户名
        password: 密码
        
    Returns:
        requests.Session 对象（已登录），失败返回 None
    """
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        session = requests.Session()
        session.verify = False  # 禁用 SSL 验证
        
        login_url = f"{backend_url.rstrip('/')}/api/account/login"
        payload = {
            "userNameOrEmailAddress": username,
            "password": password,
            "rememberMe": False
        }
        
        response = session.post(
            login_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            # ABP 框架登录成功返回格式: {"result": 1, "description": "Success"}
            # 或者包含 result 字段的其他格式
            result = data.get("result")
            if result == 1 or data.get("description") == "Success":
                # 验证登录状态
                cfg_url = f"{backend_url.rstrip('/')}/api/abp/application-configuration"
                cfg_response = session.get(cfg_url, timeout=20)
                
                if cfg_response.status_code == 200:
                    cfg_data = cfg_response.json()
                    cu = cfg_data.get("currentUser") or {}
                    if cu.get("isAuthenticated"):
                        return session
                    else:
                        print(f"❌ 登录成功但未认证，响应: {cfg_data}")
                        return None
                else:
                    print(f"❌ 验证登录状态失败，状态码: {cfg_response.status_code}")
                    return None
            else:
                print(f"❌ 登录失败，响应: {data}")
                return None
        else:
            print(f"❌ 登录失败，状态码: {response.status_code}, 响应: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录时出错: {e}")
        return None


def get_all_roles(backend_url: str, session: requests.Session) -> List[Dict]:
    """
    获取所有角色列表
    
    Args:
        backend_url: 后端 API 地址
        session: 认证 Session
        
    Returns:
        角色列表
    """
    try:
        # 使用 MaxResultCount=1000 确保获取所有角色
        roles_url = f"{backend_url.rstrip('/')}/api/identity/roles?MaxResultCount=1000"
        response = session.get(
            roles_url,
            headers={"Accept": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            roles = data.get("items", [])
            print(f"✅ 获取到 {len(roles)} 个角色")
            return roles
        else:
            print(f"❌ 获取角色列表失败，状态码: {response.status_code}, 响应: {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取角色列表时出错: {e}")
        return []


def delete_role(backend_url: str, session: requests.Session, role_id: str, role_name: str) -> bool:
    """
    删除单个角色
    
    Args:
        backend_url: 后端 API 地址
        session: 认证 Session
        role_id: 角色 ID
        role_name: 角色名称（用于日志）
        
    Returns:
        是否删除成功
    """
    try:
        delete_url = f"{backend_url.rstrip('/')}/api/identity/roles/{role_id}"
        response = session.delete(
            delete_url,
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            print(f"  ✅ 删除角色: {role_name} (ID: {role_id})")
            return True
        else:
            print(f"  ❌ 删除角色失败: {role_name} (ID: {role_id}), 状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ 删除角色时出错: {role_name} (ID: {role_id}), 错误: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("批量删除角色脚本（排除 admin 和 member）")
    print("=" * 60)
    
    # 读取配置
    backend_url = os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL)
    admin_username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    
    print(f"\n📋 配置:")
    print(f"  后端地址: {backend_url}")
    print(f"  Admin 用户: {admin_username}")
    print(f"  排除角色: {', '.join(SYSTEM_ROLES)}")
    
    # 1. 登录获取 Session
    print(f"\n🔐 正在登录...")
    session = get_auth_session(backend_url, admin_username, admin_password)
    if not session:
        print("❌ 登录失败，无法继续")
        sys.exit(1)
    print("✅ 登录成功")
    
    # 2. 获取所有角色
    print(f"\n📋 正在获取角色列表...")
    all_roles = get_all_roles(backend_url, session)
    if not all_roles:
        print("❌ 未获取到角色列表，无法继续")
        sys.exit(1)
    
    # 3. 过滤系统角色
    roles_to_delete = [
        role for role in all_roles
        if role.get("name", "").lower() not in SYSTEM_ROLES
    ]
    
    system_roles_found = [
        role for role in all_roles
        if role.get("name", "").lower() in SYSTEM_ROLES
    ]
    
    print(f"\n📊 统计:")
    print(f"  总角色数: {len(all_roles)}")
    print(f"  系统角色（保留）: {len(system_roles_found)}")
    if system_roles_found:
        print(f"    保留的角色: {', '.join([r.get('name', '') for r in system_roles_found])}")
    print(f"  待删除角色: {len(roles_to_delete)}")
    
    if not roles_to_delete:
        print("\n✅ 没有需要删除的角色")
        sys.exit(0)
    
    # 4. 确认删除
    print(f"\n⚠️  即将删除以下 {len(roles_to_delete)} 个角色:")
    for i, role in enumerate(roles_to_delete[:20], 1):  # 只显示前20个
        role_name = role.get("name", "未知")
        role_id = role.get("id", "未知")
        is_static = role.get("isStatic", False)
        static_mark = " [静态]" if is_static else ""
        print(f"  {i}. {role_name} (ID: {role_id[:8]}...){static_mark}")
    
    if len(roles_to_delete) > 20:
        print(f"  ... 还有 {len(roles_to_delete) - 20} 个角色")
    
    # 检查是否有静态角色
    static_roles = [r for r in roles_to_delete if r.get("isStatic", False)]
    if static_roles:
        print(f"\n⚠️  警告: 发现 {len(static_roles)} 个静态角色，这些角色可能无法删除")
        for role in static_roles:
            print(f"    - {role.get('name', '未知')}")
    
    # 确认
    confirm = input(f"\n❓ 确认删除这 {len(roles_to_delete)} 个角色吗？(yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("❌ 已取消删除")
        sys.exit(0)
    
    # 5. 批量删除
    print(f"\n🗑️  开始删除角色...")
    success_count = 0
    fail_count = 0
    
    for i, role in enumerate(roles_to_delete, 1):
        role_name = role.get("name", "未知")
        role_id = role.get("id", "")
        is_static = role.get("isStatic", False)
        
        print(f"[{i}/{len(roles_to_delete)}] 删除: {role_name}...", end=" ")
        
        if is_static:
            print("⏭️  跳过（静态角色）")
            fail_count += 1
            continue
        
        if delete_role(backend_url, session, role_id, role_name):
            success_count += 1
        else:
            fail_count += 1
    
    # 6. 输出结果
    print(f"\n" + "=" * 60)
    print(f"✅ 删除完成!")
    print(f"  成功: {success_count}")
    print(f"  失败/跳过: {fail_count}")
    print(f"  总计: {len(roles_to_delete)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

