#!/usr/bin/env python3
"""
# ═══════════════════════════════════════════════════════════════
# 边界值账号创建工具
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 创建用于登录边界测试的账号
# - Username 边界: 255, 256 字符
# - Password 边界: 127, 128 字符
# - Email 边界: 255, 256 字符
#
# 使用方法：
#   python3 utils/create_boundary_accounts.py
#
"""

import json
import os
import random
import ssl
import string
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

from utils.config import ConfigManager

# ABP 边界常量
ABP_MAX_USERNAME_LENGTH = 256
ABP_MAX_PASSWORD_LENGTH = 128

# 后端配置（优先从项目配置读取）
_cfg = ConfigManager()
BACKEND_URL = os.getenv("BACKEND_URL", _cfg.get_service_url("backend") or "http://localhost:5678")
APP_NAME = os.getenv("APP_NAME", "Aevatar")
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "testmail.com")

# 输出文件
BOUNDARY_ACCOUNTS_FILE = Path("test-data/boundary_accounts.json")


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _ssl_ctx() -> ssl.SSLContext:
    """本地 https 自签，跳过校验"""
    return ssl._create_unverified_context()


def _post_json(url: str, payload: Dict[str, Any], timeout_s: int = 30) -> Tuple[int, str]:
    """发送 POST JSON 请求"""
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        method="POST"
    )
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _rand_string(length: int, charset: str = string.ascii_lowercase) -> str:
    """生成指定长度的随机字符串"""
    return "".join(random.choices(charset, k=length))


def _rand_suffix(k: int = 4) -> str:
    """生成随机后缀"""
    return _rand_string(k, string.ascii_lowercase + string.digits)


def _make_strong_password(length: int) -> str:
    """
    生成指定长度的强密码（满足 ABP 密码策略）
    
    ABP 默认要求：
    - 至少 6 字符
    - 包含大写字母
    - 包含小写字母
    - 包含数字
    - 包含特殊字符
    """
    if length < 6:
        raise ValueError(f"Password length {length} is too short (min 6)")
    
    # 必须包含的字符
    required = ["A", "a", "1", "!"]
    
    # 剩余长度用随机字符填充
    remaining = length - len(required)
    charset = string.ascii_letters + string.digits + "!@#$%"
    padding = _rand_string(remaining, charset)
    
    # 组合并打乱顺序
    password_chars = list("".join(required) + padding)
    random.shuffle(password_chars)
    
    return "".join(password_chars)


def _register_account(
    username: str,
    email: str,
    password: str,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    注册账号
    
    Returns:
        (成功, 原因, 账号信息)
    """
    url = f"{BACKEND_URL.rstrip('/')}/api/account/register"
    payload = {
        "userName": username,
        "emailAddress": email,
        "password": password,
        "appName": APP_NAME,
    }
    
    status, body = _post_json(url, payload)
    
    account_info = {
        "username": username,
        "email": email,
        "password": password,
        "username_length": len(username),
        "password_length": len(password),
        "created_at": datetime.now().isoformat(),
    }
    
    if status == 200:
        return True, "ok", account_info
    
    # 解析错误信息
    reason = f"status={status}"
    if body:
        try:
            error_data = json.loads(body)
            if "error" in error_data:
                reason = error_data["error"].get("message", body[:200])
        except json.JSONDecodeError:
            reason = f"status={status} body={body[:200]}"
    
    return False, reason, account_info


# ═══════════════════════════════════════════════════════════════
# 边界账号定义
# ═══════════════════════════════════════════════════════════════

def generate_boundary_accounts() -> List[Dict[str, Any]]:
    """
    生成边界值账号配置
    
    账号类型：
    1. username_len_255: 255 字符用户名 + 正常密码
    2. username_len_256: 256 字符用户名 + 正常密码
    3. password_len_127: 正常用户名 + 127 字符密码
    4. password_len_128: 正常用户名 + 128 字符密码
    """
    timestamp = datetime.now().strftime("%m%d%H%M")
    accounts = []
    
    # ─────────────────────────────────────────────────────────────
    # Username 边界账号
    # ─────────────────────────────────────────────────────────────
    
    # 255 字符用户名 (max-1)
    # 格式: bnd_u255_{timestamp}_{随机填充到255字符}
    prefix_255 = f"bnd_u255_{timestamp}_"
    username_255 = prefix_255 + _rand_string(255 - len(prefix_255))
    accounts.append({
        "type": "username_boundary",
        "boundary": "len_255",
        "username": username_255,
        "email": f"bnd_u255_{timestamp}_{_rand_suffix()}@{EMAIL_DOMAIN}",
        "password": _make_strong_password(12),
    })
    
    # 256 字符用户名 (max)
    prefix_256 = f"bnd_u256_{timestamp}_"
    username_256 = prefix_256 + _rand_string(256 - len(prefix_256))
    accounts.append({
        "type": "username_boundary",
        "boundary": "len_256",
        "username": username_256,
        "email": f"bnd_u256_{timestamp}_{_rand_suffix()}@{EMAIL_DOMAIN}",
        "password": _make_strong_password(12),
    })
    
    # ─────────────────────────────────────────────────────────────
    # Password 边界账号
    # ─────────────────────────────────────────────────────────────
    
    # 127 字符密码 (max-1)
    accounts.append({
        "type": "password_boundary",
        "boundary": "len_127",
        "username": f"bnd_p127_{timestamp}_{_rand_suffix()}",
        "email": f"bnd_p127_{timestamp}_{_rand_suffix()}@{EMAIL_DOMAIN}",
        "password": _make_strong_password(127),
    })
    
    # 128 字符密码 (max)
    accounts.append({
        "type": "password_boundary",
        "boundary": "len_128",
        "username": f"bnd_p128_{timestamp}_{_rand_suffix()}",
        "email": f"bnd_p128_{timestamp}_{_rand_suffix()}@{EMAIL_DOMAIN}",
        "password": _make_strong_password(128),
    })
    
    # ─────────────────────────────────────────────────────────────
    # Email 边界账号
    # ─────────────────────────────────────────────────────────────
    
    # 邮箱格式: local@domain.com
    # 总长度 = local长度 + 1(@) + domain长度
    domain = EMAIL_DOMAIN  # 如 testmail.com (12字符)
    domain_with_at = f"@{domain}"  # @testmail.com (13字符)
    
    # 255 字符邮箱 (max-1)
    # local部分长度 = 255 - 13 = 242
    email_prefix_255 = f"bnd_e255_{timestamp}_"
    local_255 = email_prefix_255 + _rand_string(255 - len(domain_with_at) - len(email_prefix_255))
    email_255 = local_255 + domain_with_at
    accounts.append({
        "type": "email_boundary",
        "boundary": "len_255",
        "username": f"bnd_e255_{timestamp}_{_rand_suffix()}",
        "email": email_255,
        "password": _make_strong_password(12),
    })
    
    # 256 字符邮箱 (max)
    email_prefix_256 = f"bnd_e256_{timestamp}_"
    local_256 = email_prefix_256 + _rand_string(256 - len(domain_with_at) - len(email_prefix_256))
    email_256 = local_256 + domain_with_at
    accounts.append({
        "type": "email_boundary",
        "boundary": "len_256",
        "username": f"bnd_e256_{timestamp}_{_rand_suffix()}",
        "email": email_256,
        "password": _make_strong_password(12),
    })
    
    return accounts


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 60)
    print("边界值账号创建工具")
    print("=" * 60)
    print(f"后端地址: {BACKEND_URL}")
    print(f"应用名称: {APP_NAME}")
    print(f"邮箱域名: {EMAIL_DOMAIN}")
    print()
    
    # 生成边界账号配置
    boundary_configs = generate_boundary_accounts()
    
    created_accounts: List[Dict[str, Any]] = []
    failed_accounts: List[Dict[str, Any]] = []
    
    for config in boundary_configs:
        account_type = config["type"]
        boundary = config["boundary"]
        username = config["username"]
        email = config["email"]
        password = config["password"]
        
        print(f"\n[{account_type}:{boundary}]")
        print(f"  用户名长度: {len(username)}")
        print(f"  邮箱: {email}")
        print(f"  密码长度: {len(password)}")
        
        ok, reason, account_info = _register_account(username, email, password)
        account_info["type"] = account_type
        account_info["boundary"] = boundary
        
        if ok:
            print(f"  ✅ 注册成功")
            created_accounts.append(account_info)
        else:
            print(f"  ❌ 注册失败: {reason}")
            account_info["error"] = reason
            failed_accounts.append(account_info)
    
    # ─────────────────────────────────────────────────────────────
    # 保存结果
    # ─────────────────────────────────────────────────────────────
    
    print("\n" + "=" * 60)
    print("结果汇总")
    print("=" * 60)
    print(f"成功: {len(created_accounts)}")
    print(f"失败: {len(failed_accounts)}")
    
    if created_accounts:
        # 备份旧文件
        if BOUNDARY_ACCOUNTS_FILE.exists():
            backup = BOUNDARY_ACCOUNTS_FILE.with_suffix(
                f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            BOUNDARY_ACCOUNTS_FILE.rename(backup)
            print(f"\n旧文件备份到: {backup}")
        
        # 写入新文件
        BOUNDARY_ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "boundary_accounts": created_accounts,
            "failed_accounts": failed_accounts,
            "created_at": datetime.now().isoformat(),
            "config": {
                "backend_url": BACKEND_URL,
                "app_name": APP_NAME,
                "email_domain": EMAIL_DOMAIN,
            },
        }
        BOUNDARY_ACCOUNTS_FILE.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n✅ 账号信息已保存到: {BOUNDARY_ACCOUNTS_FILE}")
        
        # 打印账号摘要
        print("\n" + "-" * 60)
        print("已创建的边界账号：")
        print("-" * 60)
        for acc in created_accounts:
            print(f"  [{acc['type']}:{acc['boundary']}]")
            print(f"    用户名: {acc['username'][:50]}... (len={acc['username_length']})")
            print(f"    邮箱: {acc['email']}")
            print(f"    密码长度: {acc['password_length']}")
    
    if failed_accounts:
        print("\n" + "-" * 60)
        print("⚠️  失败的账号（需要检查）：")
        print("-" * 60)
        for acc in failed_accounts:
            print(f"  [{acc['type']}:{acc['boundary']}] {acc.get('error', 'unknown')}")
    
    return 0 if len(failed_accounts) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

