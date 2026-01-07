"""
Change Password - Test Helpers

规则：
- 绝不在仓库文件里写入任何真实密码/凭证
- 关键步骤截图（遵循 FAST/FULL_PAGE_SHOT 开关）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os
import random
import string

import allure
from playwright.sync_api import Page

from pages.admin_profile_change_password_page import AdminProfileChangePasswordPage
from utils.config import ConfigManager

# FAST=1：跳过高开销截图/等待，提速本地回归
FAST_MODE: bool = os.getenv("FAST", "0") == "1"
FULL_PAGE_SHOT: bool = os.getenv("FULL_PAGE_SHOT", "0") == "1"
ALLURE_SHOW_BACKEND: bool = os.getenv("ALLURE_SHOW_BACKEND", "0") == "1"
ALLURE_SHOW_META: bool = os.getenv("ALLURE_SHOW_META", "0") == "1"

_POLICY_CACHE: Optional[Dict[str, object]] = None


def step_shot(page_obj: AdminProfileChangePasswordPage, name: str, full_page: bool = False) -> None:
    """
    截图helper，支持动态全屏模式
    - 默认使用FULL_PAGE_SHOT环境变量
    - 可通过full_page参数强制全屏（用于toast等场景）
    """
    if FAST_MODE:
        return
    use_full_page = full_page or FULL_PAGE_SHOT
    page_obj.take_screenshot(name, full_page=use_full_page)


def step_shot_after_success_toast(page_obj: AdminProfileChangePasswordPage, name: str) -> None:
    """
    等待success toast出现后立即截图（全屏）
    - 用于成功场景的证据截图
    - 关键：找到toast后立即截图，避免toast自动消失
    """
    if FAST_MODE:
        return
    
    # 立即尝试找toast（不等待，避免toast已消失）
    page = page_obj.page
    toast_found = False
    
    # 策略1：立即检查toast是否已存在
    quick_selectors = [
        "text=successfully",
        "text=Success",
        "[class*='toast']",
        "[role='alert']",
    ]
    
    for sel in quick_selectors:
        try:
            if page.locator(sel).count() > 0:
                toast_found = True
                break
        except Exception:
            continue
    
    # 策略2：如果toast还没出现，等待一小段时间
    if not toast_found:
        wait_for_success_toast(page, timeout_ms=2000)
    
    # 策略3：确保toast完全渲染后立即截图（关键：立即！）
    page.wait_for_timeout(200)  # 仅200ms确保渲染完成
    page_obj.take_screenshot(name, full_page=True)


def step_shot_after_error_toast(page_obj: AdminProfileChangePasswordPage, name: str) -> None:
    """
    等待error toast出现后立即截图（全屏）
    - 用于失败场景的证据截图
    - 关键：找到toast后立即截图，避免toast自动消失
    - 策略：多轮检测 + 扩展选择器 + 充分等待
    """
    if FAST_MODE:
        return
    
    page = page_obj.page
    toast_found = False
    
    # 第一轮：立即检查error toast（扩展选择器以覆盖更多场景）
    quick_selectors = [
        "text=error",
        "text=Error",
        "text=failed",
        "text=Failed",
        "text=invalid",
        "text=Invalid",
        "text=incorrect",
        "text=Incorrect",
        "text=验证失败",
        "text=密码错误",
        "text=Password Incorrect",  # 前端实际错误消息
        "text=Validation",
        "text=validation",
        "[class*='toast']",
        "[role='alert']",
        "[class*='destructive']",  # shadcn/ui error toast
        "[class*='error']",
        "[data-state='open']",     # shadcn/ui toast state
    ]
    
    for sel in quick_selectors:
        try:
            if page.locator(sel).count() > 0:
                toast_found = True
                break
        except Exception:
            continue
    
    # 第二轮：如果toast还没出现，等待更长时间
    if not toast_found:
        wait_for_error_toast(page, timeout_ms=5000)  # 增加到5秒
    
    # 第三轮：再次检查（防止toast在等待过程中出现又消失）
    page.wait_for_timeout(300)  # 额外300ms确保toast稳定
    
    # 最终截图
    page_obj.take_screenshot(name, full_page=True)


def wait_for_success_toast(page: Page, timeout_ms: int = 3000) -> bool:
    """
    等待success toast出现
    - 返回True如果找到toast，False如果超时
    - 优化：使用最有效的选择器，减少等待时间
    """
    # 根据调试结果，最有效的选择器
    effective_selectors = [
        "text=successfully",  # 最精准
        "text=Success",       # 次选
        "[class*='toast']",   # 兜底
    ]
    
    for sel in effective_selectors:
        try:
            page.wait_for_selector(sel, state="visible", timeout=min(timeout_ms // 3, 1000))
            # 找到后不需要额外等待，立即返回让调用者截图
            return True
        except Exception:
            continue
    
    # 兜底：再次尝试用最宽泛的选择器
    try:
        page.wait_for_selector("[role='alert']", state="visible", timeout=500)
        return True
    except Exception:
        pass
    
    return False


def wait_for_error_toast(page: Page, timeout_ms: int = 5000) -> bool:
    """
    等待error toast出现
    - 返回True如果找到toast，False如果超时
    - 优化：使用最有效的选择器，扩展错误消息匹配
    """
    effective_selectors = [
        "text=error",
        "text=Error",
        "text=failed",
        "text=Failed",
        "text=invalid",
        "text=Invalid",
        "text=incorrect",
        "text=Incorrect",
        "text=Password Incorrect",  # 前端实际错误消息
        "text=验证失败",
        "text=密码错误",
        "text=Validation",
        "[class*='toast']",
        "[class*='destructive']",
        "[class*='error']",
        "[data-state='open']",
    ]
    
    for sel in effective_selectors:
        try:
            page.wait_for_selector(sel, state="visible", timeout=min(timeout_ms // 4, 1500))
            return True
        except Exception:
            continue
    
    # 兜底：用最宽泛的选择器
    try:
        page.wait_for_selector("[role='alert']", state="visible", timeout=1000)
        return True
    except Exception:
        pass
    
    return False


def attach_meta_text(name: str, text: str) -> None:
    if not ALLURE_SHOW_META:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_backend_text(name: str, text: str) -> None:
    if not ALLURE_SHOW_BACKEND:
        return
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


@dataclass(frozen=True)
class PasswordPolicy:
    required_length: int
    require_digit: bool
    require_lowercase: bool
    require_uppercase: bool
    require_non_alphanumeric: bool
    required_unique_chars: int


def fetch_abp_password_policy(auth_page: Page) -> PasswordPolicy:
    """
    从 ABP app-config 读取密码策略（真理源）。
    兼容 key: settings.values / setting.values。
    """
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        cfg = ConfigManager()
        frontend = (cfg.get_service_url("frontend") or "").rstrip("/")
        url = f"{frontend}/api/abp/application-configuration"
        data = auth_page.context.request.get(url).json()
        vals = {}
        try:
            vals = ((data.get("setting") or {}).get("values") or {}) or ((data.get("settings") or {}).get("values") or {})
        except Exception:
            vals = {}
        _POLICY_CACHE = vals or {}

    vals = _POLICY_CACHE

    def _b(k: str, default: bool) -> bool:
        v = vals.get(k, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, str) and v.lower() in {"true", "false"}:
            return v.lower() == "true"
        return bool(v)

    def _i(k: str, default: int) -> int:
        v = vals.get(k, default)
        try:
            return int(v)
        except Exception:
            return default

    policy = PasswordPolicy(
        required_length=_i("Abp.Identity.Password.RequiredLength", 6),
        require_digit=_b("Abp.Identity.Password.RequireDigit", True),
        require_lowercase=_b("Abp.Identity.Password.RequireLowercase", True),
        require_uppercase=_b("Abp.Identity.Password.RequireUppercase", True),
        require_non_alphanumeric=_b("Abp.Identity.Password.RequireNonAlphanumeric", True),
        required_unique_chars=_i("Abp.Identity.Password.RequiredUniqueChars", 1),
    )
    attach_meta_text("abp_password_policy", str(policy))
    return policy


def _rand_choice(chars: str) -> str:
    return random.choice(chars)


def generate_password(policy: PasswordPolicy, length: int, missing: str | None = None) -> str:
    """
    运行期生成密码：
    - 不在代码/文件里写死密码明文
    - 支持通过 missing 生成“缺少某一类字符”的非法密码（digit/upper/lower/special）
    """
    length = max(length, 0)

    # 字符集（不包含易引起转义/注入的控制字符）
    digits = string.digits
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    specials = "!@#$%^&*()-_=+[]{}:,.?"

    parts = []
    if policy.require_digit and missing != "digit":
        parts.append(_rand_choice(digits))
    if policy.require_lowercase and missing != "lower":
        parts.append(_rand_choice(lowers))
    if policy.require_uppercase and missing != "upper":
        parts.append(_rand_choice(uppers))
    if policy.require_non_alphanumeric and missing != "special":
        parts.append(_rand_choice(specials))

    # 至少保证 required_unique_chars：用不同字符填充前缀
    # 这里不追求“最强随机”，只求可重复跑且满足策略。
    used = set(parts)
    while len(used) < max(policy.required_unique_chars, 0):
        used.add(_rand_choice(lowers + uppers + digits + specials))
    parts = list(used)

    pool = ""
    if missing != "digit":
        pool += digits
    if missing != "lower":
        pool += lowers
    if missing != "upper":
        pool += uppers
    if missing != "special":
        pool += specials
    if not pool:
        pool = lowers  # 兜底

    while len(parts) < length:
        parts.append(_rand_choice(pool))

    random.shuffle(parts)
    return "".join(parts[:length])


def attach_no_dialog_guard(page: Page) -> Dict[str, Optional[str]]:
    """
    监听 dialog（alert/confirm/prompt），用于 XSS “不得执行”断言。
    返回 dict：{type, message}（均可能为 None）。
    """
    seen: Dict[str, Optional[str]] = {"type": None, "message": None}

    def _on_dialog(d):
        try:
            seen["type"] = getattr(d, "type", None) or "dialog"
            seen["message"] = getattr(d, "message", None)
        except Exception:
            seen["type"] = "dialog"
        try:
            d.dismiss()
        except Exception:
            pass

    try:
        page.on("dialog", _on_dialog)
    except Exception:
        pass
    return seen


