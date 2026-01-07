#!/usr/bin/env python3
"""
快速验证 Login 边界值测试账号是否可用
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.account_precheck import _abp_cookie_login_and_roles
from utils.config import ConfigManager

config = ConfigManager()


def main():
    print("=" * 70)
    print("Login 边界值测试账号验证")
    print("=" * 70)
    print()
    
    # 读取模板
    template_file = PROJECT_ROOT / "test-data" / "login_boundary_accounts_template.json"
    with open(template_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    accounts = data["test_account_pool"]
    backend_url = config.get_service_url("backend")
    
    print(f"后端地址: {backend_url}")
    print(f"待验证账号数: {len(accounts)}")
    print()
    
    available = []
    unavailable = []
    
    for i, acc in enumerate(accounts, 1):
        username = acc["username"]
        username_display = username[:30] + "..." if len(username) > 30 else username
        email = acc["email"]
        password = acc["password"]
        
        print(f"[{i}/{len(accounts)}] {username_display}")
        print(f"   Password 长度: {len(password)}")
        
        # 预检登录
        ok, reason, _roles, authenticated = _abp_cookie_login_and_roles(
            backend_url=backend_url,
            identifier=email,
            password=password,
        )
        
        if ok and authenticated:
            print(f"   ✅ 可用")
            available.append(acc)
        else:
            print(f"   ❌ 不可用: {reason}")
            unavailable.append((acc, reason))
        print()
    
    # 汇总
    print("=" * 70)
    print("验证结果")
    print("=" * 70)
    print(f"✅ 可用: {len(available)}/{len(accounts)}")
    print(f"❌ 不可用: {len(unavailable)}/{len(accounts)}")
    print()
    
    if unavailable:
        print("不可用账号详情：")
        for acc, reason in unavailable:
            username_display = acc["username"][:30] + "..." if len(acc["username"]) > 30 else acc["username"]
            print(f"  - {username_display}")
            print(f"    Email: {acc['email']}")
            print(f"    原因: {reason}")
            print()
        
        print("📝 请通过以下方式创建缺失的账号：")
        print("   1. 手动注册: https://localhost:44320/Account/Register")
        print("   2. 自动注册: python3 scripts/register_login_boundary_accounts.py")
        print()
    
    if available:
        print(f"✅ {len(available)}个账号可用，可以开始测试！")
    
    return 0 if not unavailable else 1


if __name__ == "__main__":
    sys.exit(main())

