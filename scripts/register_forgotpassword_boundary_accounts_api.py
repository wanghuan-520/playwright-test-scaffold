#!/usr/bin/env python3
"""
ForgotPassword 边界值测试账号批量注册脚本（API 版本）
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import requests

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ConfigManager

config = ConfigManager()


# ═══════════════════════════════════════════════════════════════
# 边界值账号定义（ABP Identity: email max=256）
# ═══════════════════════════════════════════════════════════════
BOUNDARY_ACCOUNTS = [
    {
        "username": "fp_email255_v2",
        "email": ("e" * 246) + "@test.com",  # 255字符（246个e + @test.com=9）
        "password": "ValidPass123!",
        "purpose": "test_p1_forgotpassword_email_length_boundaries[chromium-255]",
        "tags": ["forgotpassword_boundary", "email_255"],
    },
    {
        "username": "fp_email256_v2",
        "email": ("f" * 247) + "@test.com",  # 256字符（247个f + @test.com=9）
        "password": "ValidPass123!",
        "purpose": "test_p1_forgotpassword_email_length_boundaries[chromium-256]",
        "tags": ["forgotpassword_boundary", "email_256"],
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
        "appName": "BusinessServer",
    }
    
    print(f"\n[{BOUNDARY_ACCOUNTS.index(account) + 1}/{len(BOUNDARY_ACCOUNTS)}] 注册账号: {account['username'][:30]}...")
    print(f"  🔗 POST {api_url}")
    print(f"     username: {account['username'][:30]}... (len={len(account['username'])})")
    print(f"     email: {account['email'][:30]}... (len={len(account['email'])})")
    print(f"     password: {'*' * 13} (len={len(account['password'])})")
    
    try:
        resp = requests.post(
            api_url,
            json=payload,
            verify=False,  # 开发环境自签名证书
            timeout=15,
        )
        print(f"  📡 Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"  ✅ 注册成功")
            return True, "success"
        else:
            reason = resp.text[:200] if resp.text else f"http_{resp.status_code}"
            print(f"  ❌ 注册失败: {reason}")
            return False, reason
    except Exception as e:
        reason = f"exception: {str(e)[:100]}"
        print(f"  ❌ 注册失败: {reason}")
        return False, reason


def add_to_account_pool(account: Dict, pool_path: Path):
    """添加账号到账号池"""
    if not pool_path.exists():
        pool_data = {"test_account_pool": []}
    else:
        with open(pool_path) as f:
            pool_data = json.load(f)
    
    # 检查是否已存在
    existing = pool_data.get("test_account_pool", [])
    for acc in existing:
        if acc.get("username") == account["username"]:
            print(f"  ⚠️  账号已存在: {account['username']}")
            return
    
    # 添加新账号
    existing.append({
        "username": account["username"],
        "email": account["email"],
        "password": account["password"],
        "tags": account.get("tags", []),
        "purpose": account.get("purpose", ""),
        "note": account.get("note", ""),
    })
    pool_data["test_account_pool"] = existing
    
    # 保存
    with open(pool_path, "w") as f:
        json.dump(pool_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 添加到账号池: {account['username'][:30]}...")


def main():
    backend_url = config.get_service_url("backend")
    if not backend_url:
        print("❌ 错误：无法获取 backend URL")
        sys.exit(1)
    
    print(f"Backend URL: {backend_url}")
    print(f"待注册账号数: {len(BOUNDARY_ACCOUNTS)}")
    print("=" * 70)
    
    results = []
    for account in BOUNDARY_ACCOUNTS:
        success, reason = register_account_via_api(backend_url, account)
        results.append((account, success, reason))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("注册结果汇总")
    print("=" * 70)
    success_count = sum(1 for _, s, _ in results if s)
    failed_count = len(results) - success_count
    print(f"✅ 成功: {success_count}个")
    print(f"❌ 失败: {failed_count}个")
    
    if failed_count > 0:
        print("\n失败详情：")
        for account, success, reason in results:
            if not success:
                print(f"  - {account['username'][:30]}...")
                print(f"    原因: {reason[:100]}")
    
    # 更新账号池
    print("\n" + "=" * 70)
    print("🔄 更新账号池...")
    account_pool_path = PROJECT_ROOT / "test-data" / "test_account_pool.json"
    
    added_count = 0
    for account, success, reason in results:
        if success:
            add_to_account_pool(account, account_pool_path)
            added_count += 1
    
    print(f"\n✅ 账号池已更新: {account_pool_path}")
    print(f"   新增账号: {added_count}个")
    
    print("\n" + "=" * 70)
    print("完成！")
    print("=" * 70)
    
    if failed_count > 0:
        print("\n⚠️  部分账号注册失败，请手动创建或调整测试策略")
    
    print("\n📝 下一步：")
    print("   1. 运行测试: make test TESTS=tests/Account/ForgotPassword/test_ForgotPassword_p1_abp_constraints.py")


if __name__ == "__main__":
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()

