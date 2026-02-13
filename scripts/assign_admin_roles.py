#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# 给 TestAdmin1~10 赋 admin 角色、移除 member 角色
# ═══════════════════════════════════════════════════════════════
"""
通过 ABP Identity API 批量管理用户角色。
使用默认 admin 账号登录后在浏览器上下文中操作。
"""

import json
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:5173"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1q2w3E*"
TARGET_PREFIX = "TestAdmin"


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 720},
        )
        page = ctx.new_page()

        # ─── 1. 登录 admin ────────────────────────────────────
        print("🔐 登录 admin 账号...")
        page.goto(f"{FRONTEND_URL}/login", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector('input[placeholder="Enter username or email"]', state="visible", timeout=10000)
        page.fill('input[placeholder="Enter username or email"]', ADMIN_USERNAME)
        page.fill('input[placeholder="Enter your password"]', ADMIN_PASSWORD)
        page.click('button:has-text("Sign In")')
        page.wait_for_timeout(2000)

        if "/login" in page.url:
            print("❌ admin 登录失败")
            ctx.close()
            browser.close()
            return

        print(f"✅ 登录成功 (url={page.url})")

        # ─── 2. 获取角色列表 ──────────────────────────────────
        print("\n📋 获取角色列表...")
        roles_data = page.evaluate("""async () => {
            const r = await fetch('/api/identity/roles');
            if (!r.ok) return { error: r.status };
            return await r.json();
        }""")

        if "error" in roles_data:
            print(f"❌ 获取角色失败: {roles_data}")
            ctx.close()
            browser.close()
            return

        roles = roles_data.get("items", [])
        role_map = {r["name"].lower(): r for r in roles}
        print(f"   角色列表: {[r['name'] for r in roles]}")

        admin_role = role_map.get("admin")
        member_role = role_map.get("member")

        if not admin_role:
            print("❌ 未找到 admin 角色")
            ctx.close()
            browser.close()
            return

        print(f"   admin 角色 ID: {admin_role['id']}")
        if member_role:
            print(f"   member 角色 ID: {member_role['id']}")

        # ─── 3. 查找 TestAdmin 用户 ──────────────────────────
        print(f"\n🔍 查找 {TARGET_PREFIX} 用户...")
        users_data = page.evaluate("""async (prefix) => {
            const r = await fetch(`/api/identity/users?filter=${prefix}&maxResultCount=20`);
            if (!r.ok) return { error: r.status };
            return await r.json();
        }""", TARGET_PREFIX)

        if "error" in users_data:
            print(f"❌ 查找用户失败: {users_data}")
            ctx.close()
            browser.close()
            return

        users = users_data.get("items", [])
        target_users = [u for u in users if u["userName"].startswith(TARGET_PREFIX)]
        print(f"   找到 {len(target_users)} 个 TestAdmin 用户")

        # ─── 4. 逐个设置角色 ─────────────────────────────────
        print("\n🔧 设置角色...\n" + "=" * 60)

        for user in sorted(target_users, key=lambda u: u["userName"]):
            uid = user["id"]
            uname = user["userName"]

            # 获取当前角色
            current_roles = page.evaluate("""async (userId) => {
                const r = await fetch(`/api/identity/users/${userId}/roles`);
                if (!r.ok) return { error: r.status };
                return await r.json();
            }""", uid)

            current_role_names = [r["name"] for r in current_roles.get("items", [])]
            print(f"[{uname}] 当前角色: {current_role_names}", end=" → ")

            # 构造新角色列表：加 admin，去 member
            new_roles = ["admin"]
            for rn in current_role_names:
                if rn.lower() not in ("admin", "member"):
                    new_roles.append(rn)

            # 设置新角色
            result = page.evaluate("""async ({userId, roleNames}) => {
                const r = await fetch(`/api/identity/users/${userId}/roles`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ roleNames })
                });
                if (!r.ok) {
                    const text = await r.text();
                    return { error: r.status, body: text.substring(0, 200) };
                }
                return { ok: true };
            }""", {"userId": uid, "roleNames": new_roles})

            if result.get("ok"):
                print(f"✅ 新角色: {new_roles}")
            else:
                print(f"❌ 失败: {result}")

        # ─── 5. 验证 ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("🔍 验证角色设置...\n")

        for user in sorted(target_users, key=lambda u: u["userName"]):
            uid = user["id"]
            uname = user["userName"]

            verify = page.evaluate("""async (userId) => {
                const r = await fetch(`/api/identity/users/${userId}/roles`);
                if (!r.ok) return { error: r.status };
                return await r.json();
            }""", uid)

            role_names = [r["name"] for r in verify.get("items", [])]
            has_admin = "admin" in role_names
            has_member = "member" in role_names
            status = "✅" if has_admin and not has_member else "⚠️"
            print(f"  {status} {uname}: {role_names}")

        ctx.close()
        browser.close()
        print("\n🏁 完成")


if __name__ == "__main__":
    main()
