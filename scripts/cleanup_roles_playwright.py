#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Playwright 清理测试产生的多余角色

用法：
    python scripts/cleanup_roles_playwright.py
"""

import sys
import os
import time

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

# 系统保留角色（不会被删除）
RESERVED_ROLES = {"admin", "member"}

# 后端 API URL
BACKEND_URL = "http://localhost:5678"
FRONTEND_URL = "http://localhost:5173"


def cleanup_roles():
    """清理测试角色"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 无头模式
        context = browser.new_context()
        page = context.new_page()
        
        print("=" * 50)
        print("开始清理测试角色")
        print("=" * 50)
        
        # 1. 先登录
        print("\n1. 登录管理员账号...")
        page.goto(f"{FRONTEND_URL}/login")
        page.wait_for_timeout(2000)
        
        # 填写登录表单
        page.fill('input[type="email"], input[name="email"], #email, input[placeholder*="email" i]', 'admin@abp.io')
        page.fill('input[type="password"], input[name="password"], #password', '1q2w3E*')
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        
        print("   登录完成")
        
        # 2. 通过 API 获取所有角色
        print("\n2. 获取所有角色...")
        
        try:
            response = page.request.get(
                f"{BACKEND_URL}/api/identity/roles?MaxResultCount=1000",
                headers={"Accept": "application/json"}
            )
            
            if response.status != 200:
                print(f"   获取角色列表失败: {response.status}")
                browser.close()
                return
            
            roles = response.json().get("items", [])
            print(f"   共 {len(roles)} 个角色")
            
        except Exception as e:
            print(f"   获取角色列表失败: {e}")
            browser.close()
            return
        
        # 3. 分类角色
        roles_to_delete = []
        roles_to_keep = []
        
        for role in roles:
            role_name = role.get("name", "")
            is_static = role.get("isStatic", False)
            role_id = role.get("id", "")
            
            # 系统角色（static）不删除
            if is_static:
                roles_to_keep.append(role_name)
                continue
            
            # 保留角色不删除
            if role_name.lower() in RESERVED_ROLES:
                roles_to_keep.append(role_name)
                continue
            
            # 其他角色都删除
            roles_to_delete.append({"id": role_id, "name": role_name})
        
        print(f"\n3. 角色分析:")
        print(f"   保留角色 ({len(roles_to_keep)}): {', '.join(roles_to_keep)}")
        print(f"   待删除角色 ({len(roles_to_delete)}): {', '.join([r['name'] for r in roles_to_delete])}")
        
        if not roles_to_delete:
            print("\n没有需要删除的角色")
            browser.close()
            return
        
        # 4. 删除角色
        print(f"\n4. 开始删除 {len(roles_to_delete)} 个角色...")
        
        deleted = 0
        failed = 0
        
        for role in roles_to_delete:
            role_id = role["id"]
            role_name = role["name"]
            
            try:
                delete_response = page.request.delete(
                    f"{BACKEND_URL}/api/identity/roles/{role_id}",
                    headers={"Accept": "application/json"}
                )
                
                if delete_response.status in [200, 204]:
                    print(f"   ✓ 已删除: {role_name}")
                    deleted += 1
                else:
                    print(f"   ✗ 删除失败: {role_name} (状态码: {delete_response.status})")
                    failed += 1
                    
            except Exception as e:
                print(f"   ✗ 删除出错: {role_name} ({e})")
                failed += 1
            
            time.sleep(0.3)  # 避免请求过快
        
        print("\n" + "=" * 50)
        print(f"清理完成: 删除 {deleted} 个，失败 {failed} 个，保留 {len(roles_to_keep)} 个")
        print("=" * 50)
        
        # 5. 验证结果
        print("\n5. 验证清理结果...")
        page.goto(f"{FRONTEND_URL}/admin/roles")
        page.wait_for_timeout(3000)
        
        # 再次获取角色列表
        verify_response = page.request.get(
            f"{BACKEND_URL}/api/identity/roles?MaxResultCount=1000",
            headers={"Accept": "application/json"}
        )
        
        if verify_response.status == 200:
            remaining_roles = verify_response.json().get("items", [])
            print(f"   剩余角色数量: {len(remaining_roles)}")
            for role in remaining_roles:
                print(f"     - {role.get('name')} (static={role.get('isStatic')})")
        
        page.wait_for_timeout(2000)
        browser.close()
        print("\n清理脚本执行完毕")


if __name__ == "__main__":
    cleanup_roles()
