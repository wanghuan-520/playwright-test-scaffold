#!/usr/bin/env python3
"""
Login 边界值测试账号批量注册脚本（API 版本）

优点：
1. 直接调用后端 API，不依赖 UI
2. 速度快，无浏览器开销
3. 更稳定，不受前端变化影响
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import requests

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ConfigManager

config = ConfigManager()


# ═══════════════════════════════════════════════════════════════
# 边界值账号定义（ABP Identity: username max=256, password max=128）
# ═══════════════════════════════════════════════════════════════
BOUNDARY_ACCOUNTS = [
    {
        "username": "login_pass127_user",
        "email": "login_pass127@example.com",
        "password": "P" + "1" * 124 + "a!",  # 127字符 (P + 124个1 + a!)
        "purpose": "test_p1_login_password_length_boundaries[chromium-127]",
        "tags": ["login_boundary", "password_127"],
    },
    {
        "username": "login_pass128_user",
        "email": "login_pass128@example.com",
        "password": "P" + "1" * 125 + "a!",  # 128字符 (P + 125个1 + a!)
        "purpose": "test_p1_login_password_length_boundaries[chromium-128]",
        "tags": ["login_boundary", "password_128"],
    },
    {
        "username": "login_pass129_user",
        "email": "login_pass129@example.com",
        "password": "P" + "1" * 126 + "a!",  # 129字符 (P + 126个1 + a!) ⚠️
        "purpose": "test_p1_login_password_length_boundaries[chromium-129]",
        "tags": ["login_boundary", "password_129"],
        "note": "⚠️ password=129 超过 ABP 约束(128)，预期注册失败",
    },
    {
        "username": "u" * 255,  # 255字符
        "email": "login_user255@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_username_length_boundaries[chromium-255]",
        "tags": ["login_boundary", "username_255"],
    },
    {
        # ✅ 使用混合字符避免与已存在账号冲突，同时保持长度=256
        "username": "a" + "b" * 254 + "c",  # 256字符（a + 254个b + c）
        "email": "login_user256_new@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_username_length_boundaries[chromium-256]",
        "tags": ["login_boundary", "username_256"],
    },
    {
        # ✅ username=257（N+1 边界值）
        "username": "x" + "y" * 255 + "z",  # 257字符（x + 255个y + z）
        "email": "login_user257@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_username_length_boundaries[chromium-257]",
        "tags": ["login_boundary", "username_257"],
        "note": "⚠️ username=257 超过 ABP 约束(256)，预期注册失败",
    },
    {
        "username": "login_required_test_user1",
        "email": "login_required1@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_required_fields_validation[chromium-username_or_email-#LoginInput_UserNameOrEmailAddress]",
        "tags": ["login_required"],
    },
    {
        "username": "login_required_test_user2",
        "email": "login_required2@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_required_fields_validation[chromium-password-#LoginInput_Password]",
        "tags": ["login_required"],
    },
]


def register_account_via_api(backend_url: str, account: Dict) -> Tuple[bool, str]:
    """
    通过 API 注册账号
    
    Args:
        backend_url: 后端地址（如 https://localhost:44320）
        account: 账号信息
    
    Returns:
        (success: bool, reason: str)
    """
    api_url = f"{backend_url}/api/account/register"
    
    payload = {
        "userName": account["username"],
        "emailAddress": account["email"],
        "password": account["password"],
        "appName": "MVC",  # ABP 默认 AppName
    }
    
    try:
        print(f"  🔗 POST {api_url}")
        print(f"     username: {account['username'][:30]}... (len={len(account['username'])})")
        print(f"     password: {'*' * len(account['password'])} (len={len(account['password'])})")
        
        response = requests.post(
            api_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            verify=False,  # 忽略 HTTPS 证书警告（本地开发环境）
            timeout=30,
        )
        
        print(f"  📡 Status: {response.status_code}")
        
        # 成功：2xx
        if 200 <= response.status_code < 300:
            print(f"  ✅ 注册成功")
            return True, "success"
        
        # 失败：解析错误信息
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "")
            if not error_message:
                error_message = error_data.get("message", "")
            if not error_message:
                error_message = str(error_data)
        except Exception:
            error_message = response.text[:200]
        
        # 特殊处理：password=33 的预期失败
        if len(account["password"]) > 32:
            print(f"  ⚠️  注册失败（预期）：password={len(account['password'])} 超过 ABP 约束(32)")
            return False, f"password_too_long_{len(account['password'])}"
        
        print(f"  ❌ 注册失败: {error_message}")
        return False, error_message
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ 注册失败（网络异常）: {e}")
        return False, f"network_error: {e}"
    except Exception as e:
        print(f"  ❌ 注册失败（未知异常）: {e}")
        return False, f"exception: {e}"


def update_account_pool(accounts: List[Dict]) -> None:
    """
    更新 test_account_pool.json
    """
    pool_file = PROJECT_ROOT / "test-data" / "test_account_pool.json"
    
    # 读取现有账号池
    if pool_file.exists():
        with open(pool_file, "r", encoding="utf-8") as f:
            pool_data = json.load(f)
    else:
        pool_data = {"test_account_pool": [], "pool_config": {}}
    
    existing_usernames = {acc["username"] for acc in pool_data.get("test_account_pool", [])}
    
    # 添加新账号（去重）
    added = 0
    for acc in accounts:
        if acc["username"] not in existing_usernames:
            pool_data["test_account_pool"].append({
                "username": acc["username"],
                "email": acc["email"],
                "password": acc["password"],
                "initial_password": acc["password"],
                "in_use": False,
                "is_locked": False,
                "roles": ["default"],
                "tags": acc.get("tags", []),
                "purpose": acc.get("purpose", ""),
                "note": acc.get("note", ""),
            })
            added += 1
            print(f"  ✅ 添加到账号池: {acc['username'][:30]}...")
        else:
            print(f"  ⏭️  已存在，跳过: {acc['username'][:30]}...")
    
    # 保存
    if added > 0:
        with open(pool_file, "w", encoding="utf-8") as f:
            json.dump(pool_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 账号池已更新: {pool_file}")
        print(f"   新增账号: {added}个")
    else:
        print(f"\n⏭️  无新增账号")


def main():
    print("=" * 70)
    print("Login 边界值测试账号批量注册（API 版本）")
    print("=" * 70)
    print(f"\n📋 待注册账号数量: {len(BOUNDARY_ACCOUNTS)}")
    print()
    
    # 显示账号列表
    for i, acc in enumerate(BOUNDARY_ACCOUNTS, 1):
        username_display = acc["username"][:30] + "..." if len(acc["username"]) > 30 else acc["username"]
        print(f"{i}. {username_display}")
        print(f"   Email: {acc['email']}")
        print(f"   Password: {'*' * len(acc['password'])} (长度={len(acc['password'])})")
        print(f"   用途: {acc.get('purpose', 'N/A')[:80]}")
        if "note" in acc:
            print(f"   ⚠️  {acc['note']}")
        print()
    
    # 检查是否在交互式终端
    if sys.stdin.isatty():
        input("按 Enter 继续注册...")
    else:
        print("⚙️  非交互模式，自动继续...")
    print()
    
    # 获取后端地址
    backend_url = config.get_service_url("backend")
    if not backend_url:
        print("❌ 错误：无法获取后端地址，请检查配置")
        return 1
    
    print(f"🔗 后端地址: {backend_url}")
    print(f"📡 API 端点: {backend_url}/api/account/register")
    print()
    
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 批量注册
    success_accounts = []
    failed_accounts = []
    
    for i, acc in enumerate(BOUNDARY_ACCOUNTS, 1):
        print(f"\n[{i}/{len(BOUNDARY_ACCOUNTS)}] 注册账号: {acc['username'][:30]}...")
        
        success, reason = register_account_via_api(backend_url, acc)
        
        if success:
            success_accounts.append(acc)
        else:
            failed_accounts.append((acc, reason))
        
        # 等待一下，避免频率限制
        time.sleep(1)
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("注册结果汇总")
    print("=" * 70)
    print(f"✅ 成功: {len(success_accounts)}个")
    print(f"❌ 失败: {len(failed_accounts)}个")
    print()
    
    if failed_accounts:
        print("失败详情：")
        for acc, reason in failed_accounts:
            username_display = acc['username'][:30] + "..." if len(acc['username']) > 30 else acc['username']
            print(f"  - {username_display}")
            print(f"    原因: {reason[:100]}")
        print()
    
    # 更新账号池（只添加成功的）
    if success_accounts:
        print("\n🔄 更新账号池...")
        update_account_pool(success_accounts)
    
    print("\n" + "=" * 70)
    print("完成！")
    print("=" * 70)
    
    if failed_accounts:
        print("\n⚠️  部分账号注册失败，请手动创建或调整测试策略")
        print("   详见: test-data/LOGIN_BOUNDARY_ACCOUNTS.md")
    
    print("\n📝 下一步：")
    print("   1. 验证账号可用性: python3 scripts/verify_login_boundary_accounts.py")
    print("   2. 运行测试: make test TESTS=tests/Account/Login/test_Login_p1_abp_constraints.py")
    
    return 0 if not failed_accounts else 1


if __name__ == "__main__":
    sys.exit(main())

