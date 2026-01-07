#!/usr/bin/env python3
"""
Login 边界值测试账号批量注册脚本

功能：
1. 批量注册 Login 边界值测试所需的特殊账号
2. 自动添加到 test_account_pool.json
3. 验证账号可用性

账号列表：
- login_pass31_user (password=31字符)
- login_pass32_user (password=32字符)
- login_pass33_user (password=33字符) ⚠️ 可能失败
- login_user255 (username=255字符)
- login_user256 (username=256字符)
- login_required_test_user1/2 (必填验证)
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

from playwright.sync_api import sync_playwright, Page

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import ConfigManager

config = ConfigManager()


# ═══════════════════════════════════════════════════════════════
# 边界值账号定义
# ═══════════════════════════════════════════════════════════════
BOUNDARY_ACCOUNTS = [
    {
        "username": "login_pass31_user",
        "email": "login_pass31@example.com",
        "password": "P" + "1" * 28 + "a!",  # 31字符 (P + 28个1 + a!)
        "purpose": "test_p1_login_password_length_boundaries[chromium-31]",
        "tags": ["login_boundary", "password_31"],
    },
    {
        "username": "login_pass32_user",
        "email": "login_pass32@example.com",
        "password": "P" + "1" * 29 + "a!",  # 32字符 (P + 29个1 + a!)
        "purpose": "test_p1_login_password_length_boundaries[chromium-32]",
        "tags": ["login_boundary", "password_32"],
    },
    {
        "username": "login_pass33_user",
        "email": "login_pass33@example.com",
        "password": "P" + "1" * 30 + "a!",  # 33字符 (P + 30个1 + a!) ⚠️
        "purpose": "test_p1_login_password_length_boundaries[chromium-33]",
        "tags": ["login_boundary", "password_33"],
        "note": "⚠️ password=33 超过 ABP 约束(32)，可能注册失败",
    },
    {
        "username": "u" * 255,  # 255字符
        "email": "login_user255@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_username_length_boundaries[chromium-255]",
        "tags": ["login_boundary", "username_255"],
    },
    {
        "username": "u" * 256,  # 256字符
        "email": "login_user256@example.com",
        "password": "ValidPass123!",
        "purpose": "test_p1_login_username_length_boundaries[chromium-256]",
        "tags": ["login_boundary", "username_256"],
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


def register_account_via_ui(page: Page, account: Dict) -> tuple[bool, str]:
    """
    通过 UI 注册账号
    
    Returns:
        (success: bool, reason: str)
    """
    backend_url = config.get_service_url("backend")
    register_url = f"{backend_url}/Account/Register"
    
    try:
        print(f"  🔗 导航到注册页: {register_url}")
        page.goto(register_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1000)
        
        # 填写表单
        print(f"  📝 填写注册表单...")
        page.fill("#RegisterInput_UserName", account["username"])
        page.fill("#RegisterInput_EmailAddress", account["email"])
        page.fill("#RegisterInput_Password", account["password"])
        page.wait_for_timeout(500)
        
        # 提交
        print(f"  ✅ 提交注册...")
        page.click("button[name='Action'][type='submit']")
        page.wait_for_timeout(3000)
        
        # 检查结果
        current_url = page.url or ""
        
        # 成功：跳转离开注册页
        if "/Account/Register" not in current_url:
            print(f"  ✅ 注册成功（跳转到: {current_url}）")
            return True, "success"
        
        # 失败：仍在注册页，检查错误信息
        error_text = ""
        try:
            error_locator = page.locator(".validation-summary-errors, .alert-danger, .text-danger")
            if error_locator.count() > 0:
                error_text = error_locator.first.inner_text()
        except Exception:
            pass
        
        # 特殊处理：password=33 的预期失败
        if len(account["password"]) > 32:
            print(f"  ⚠️  注册失败（预期）：password={len(account['password'])} 超过 ABP 约束(32)")
            return False, f"password_too_long_{len(account['password'])}"
        
        print(f"  ❌ 注册失败: {error_text or '未知原因'}")
        return False, error_text or "unknown_error"
        
    except Exception as e:
        print(f"  ❌ 注册失败（异常）: {e}")
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
            print(f"  ✅ 添加到账号池: {acc['username']}")
        else:
            print(f"  ⏭️  已存在，跳过: {acc['username']}")
    
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
    print("Login 边界值测试账号批量注册")
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
    import sys
    if sys.stdin.isatty():
        input("按 Enter 继续注册...")
    else:
        print("⚙️  非交互模式，自动继续...")
    print()
    
    # 使用 Playwright 注册
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 可视化执行，便于观察
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        success_accounts = []
        failed_accounts = []
        
        for i, acc in enumerate(BOUNDARY_ACCOUNTS, 1):
            print(f"\n[{i}/{len(BOUNDARY_ACCOUNTS)}] 注册账号: {acc['username'][:30]}...")
            
            success, reason = register_account_via_ui(page, acc)
            
            if success:
                success_accounts.append(acc)
            else:
                failed_accounts.append((acc, reason))
            
            # 等待一下，避免频率限制
            time.sleep(2)
        
        browser.close()
    
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
            print(f"  - {acc['username'][:30]}: {reason}")
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
    
    return 0 if not failed_accounts else 1


if __name__ == "__main__":
    sys.exit(main())

