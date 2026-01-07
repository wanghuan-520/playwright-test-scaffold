#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
账号池管理脚本：添加 admin 账号
功能：
1. 添加 10 个 admin 账号到账号池顶部
2. 为所有账号添加 role 字段（admin/user）
"""

import json
from datetime import datetime
from pathlib import Path


def add_admin_accounts():
    """添加 admin 账号到账号池"""
    
    # 文件路径
    pool_path = Path(__file__).parent.parent / "test-data" / "test_account_pool.json"
    
    # 读取现有账号池
    print("📖 读取现有账号池...")
    with open(pool_path, 'r', encoding='utf-8') as f:
        pool_data = json.load(f)
    
    existing_accounts = pool_data.get("test_account_pool", [])
    pool_config = pool_data.get("pool_config", {})
    
    print(f"✅ 现有账号数量: {len(existing_accounts)}")
    
    # 创建 10 个 admin 账号
    print("\n🔨 创建 10 个 admin 账号...")
    admin_accounts = []
    current_time = datetime.now().isoformat()
    
    for i in range(1, 11):
        admin_account = {
            "username": f"admin-test{i:02d}",
            "email": f"admin-test{i:02d}@test.com",
            "password": "Wh520520!",
            "initial_password": "Wh520520!",
            "role": "admin",
            "in_use": False,
            "is_locked": False,
            "last_used": None,
            "account_type": "auth"
        }
        admin_accounts.append(admin_account)
        print(f"  ✓ 创建 admin 账号: {admin_account['email']}")
    
    # 为现有账号添加 role 字段（标记为普通用户）
    print("\n🏷️  为现有账号添加 role 字段...")
    for account in existing_accounts:
        if "role" not in account:
            account["role"] = "user"
    
    print(f"  ✓ 已为 {len(existing_accounts)} 个现有账号添加 role='user'")
    
    # 合并账号（admin 账号在前）
    new_accounts = admin_accounts + existing_accounts
    
    # 更新池配置
    pool_config["pool_size"] = len(new_accounts)
    
    # 保存新的账号池
    new_pool_data = {
        "test_account_pool": new_accounts,
        "pool_config": pool_config
    }
    
    # 备份原文件
    backup_path = pool_path.parent / f"test_account_pool_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n💾 备份原账号池到: {backup_path.name}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(pool_data, f, indent=2, ensure_ascii=False)
    
    # 写入新账号池
    print(f"✍️  写入新账号池...")
    with open(pool_path, 'w', encoding='utf-8') as f:
        json.dump(new_pool_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 完成！账号池已更新")
    print(f"\n📊 统计信息:")
    print(f"  - Admin 账号: {len(admin_accounts)}")
    print(f"  - 普通账号: {len(existing_accounts)}")
    print(f"  - 总计: {len(new_accounts)}")
    
    print(f"\n🔑 Admin 账号列表:")
    for account in admin_accounts:
        print(f"  - {account['email']} (密码: {account['password']})")


if __name__ == "__main__":
    add_admin_accounts()

