#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# 批量注册账号脚本（后端 API 方式）
# ═══════════════════════════════════════════════════════════════
"""
从 test_account_pool.json 读取所有账号，
通过后端 /api/account/register 接口批量注册。

用法:
    python3 scripts/register_accounts.py
    python3 scripts/register_accounts.py --base-url http://localhost:5173
"""

import json
import sys
import time
import argparse
from pathlib import Path
from urllib import request, error

# ─── 配置 ────────────────────────────────────────────────────
POOL_PATH = Path(__file__).parent.parent / "test-data" / "test_account_pool.json"
APP_NAME = "VibeResearching"
REGISTER_ENDPOINT = "/api/account/register"


def load_accounts():
    """加载账号池"""
    with open(POOL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("test_account_pool", [])


def register_one(base_url: str, account: dict) -> tuple:
    """
    注册单个账号，返回 (success, http_code, message)
    """
    username = account["username"]
    email = account["email"]
    password = account.get("initial_password") or account["password"]

    payload = json.dumps({
        "appName": APP_NAME,
        "userName": username,
        "emailAddress": email,
        "password": password,
    }).encode("utf-8")

    url = f"{base_url.rstrip('/')}{REGISTER_ENDPOINT}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, resp.status, body[:200]
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        # 解析 ABP 错误
        try:
            err_data = json.loads(body)
            err_msg = err_data.get("error", {}).get("message", "")
            err_detail = err_data.get("error", {}).get("details", "")
            validations = err_data.get("error", {}).get("validationErrors", [])

            # 判断"已存在"
            indicators = ["taken", "exist", "duplicate", "已被使用", "已存在"]
            combined = f"{err_msg} {err_detail}".lower()
            if any(kw in combined for kw in indicators):
                return False, e.code, f"already_exists: {err_msg}"
            if validations:
                v_msgs = [v.get("message", "") for v in validations]
                return False, e.code, f"validation: {'; '.join(v_msgs)}"

            return False, e.code, f"{err_msg} | {err_detail}"
        except json.JSONDecodeError:
            return False, e.code, body[:200]
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def main():
    parser = argparse.ArgumentParser(description="批量注册账号")
    parser.add_argument(
        "--base-url",
        default="http://localhost:5173",
        help="后端或前端代理地址 (默认: http://localhost:5173)",
    )
    args = parser.parse_args()

    accounts = load_accounts()
    print(f"📋 账号池共 {len(accounts)} 个账号")
    print(f"🔗 API 地址: {args.base_url}{REGISTER_ENDPOINT}")
    print(f"📦 appName: {APP_NAME}")
    print("=" * 64)

    results = {"success": [], "already_exists": [], "failed": []}

    for i, acc in enumerate(accounts, 1):
        username = acc["username"]
        email = acc["email"]

        print(f"[{i:02d}/{len(accounts)}] {username} ({email})...", end=" ", flush=True)

        ok, code, msg = register_one(args.base_url, acc)

        if ok:
            print(f"✅ 成功 (HTTP {code})")
            results["success"].append(username)
        elif "already_exists" in msg:
            print(f"⏭️  已存在 (HTTP {code})")
            results["already_exists"].append(username)
        else:
            print(f"❌ 失败 (HTTP {code}: {msg})")
            results["failed"].append((username, f"HTTP {code}: {msg}"))

        time.sleep(0.3)

    # ─── 汇总 ────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("📊 注册结果汇总")
    print("=" * 64)
    print(f"  ✅ 成功注册:  {len(results['success'])}")
    for u in results["success"]:
        print(f"     - {u}")
    print(f"  ⏭️  已存在:    {len(results['already_exists'])}")
    for u in results["already_exists"]:
        print(f"     - {u}")
    print(f"  ❌ 失败:      {len(results['failed'])}")
    for u, r in results["failed"]:
        print(f"     - {u}: {r}")

    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
