# ═══════════════════════════════════════════════════════════════
# Admin Users Roles - Helpers
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Dict, Optional

import pytest
import allure
from playwright.sync_api import Page, Response, expect
from pages.admin_roles_page import AdminRolesPage
from utils.logger import get_logger

logger = get_logger(__name__)


URL_PATH = '/admin/roles'


# 字段规则
FIELD_RULES = [
    {
        'field': 'search',
        'selector': 'role=searchbox',
        'required': None,
        'min_len': None,
        'max_len': None,
        'pattern': None,
        'html_type': 'text',
    }
]

ERROR_SELECTORS = [
    ".invalid-feedback",
    ".text-danger",
    ".error-message",
    ".field-error",
    ".toast-error",
    ".Toastify__toast--error",
    "p.text-red-500",
    ".sonner-toast[data-type='error']",
]


def assert_not_redirected_to_login(page: Page) -> None:
    """断言未被重定向到登录页"""
    url = page.url or ""
    assert "/auth/login" not in url, f"redirected to frontend login: {url}"
    assert "/Account/Login" not in url, f"redirected to ABP login: {url}"
    assert "/login" not in url.lower(), f"redirected to login: {url}"


def click_save(page: Page) -> None:
    """点击保存按钮"""
    candidates = [
        'button:has-text("Save")',
        'button:has-text("保存")',
        'button[type="submit"]:has-text("Save")',
        'button[type="submit"]:has-text("保存")',
    ]
    for sel in candidates:
        btn = page.locator(sel).first
        try:
            if btn.count() == 0:
                continue
            if not btn.is_visible(timeout=800):
                continue
            expect(btn).to_be_enabled()
            btn.click()
            return
        except Exception:
            continue
    pytest.skip(f"页面不存在 Save/保存 按钮：跳过需要保存动作的模板用例。url={page.url}")


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    """等待写操作响应（PUT/POST/PATCH）"""
    try:
        with page.expect_response(
            lambda r: (r.request.method in ("PUT", "POST", "PATCH")), 
            timeout=timeout_ms
        ) as resp_info:
            pass
        return resp_info.value
    except Exception:
        return None


def wait_response_by_url_substring(
    page: Page, 
    url_substring: str, 
    *, 
    method: str = "POST", 
    timeout_ms: int = 60000
) -> Response:
    """等待指定 URL 子串的响应"""
    with page.expect_response(
        lambda r: (r.request.method == method) and (url_substring in (r.url or "")),
        timeout=timeout_ms,
    ) as resp_info:
        pass
    return resp_info.value


def get_validation_message(page: Page, selector: str) -> str:
    """读取浏览器原生表单校验文案"""
    if not selector or page.locator(selector).count() == 0:
        return ""
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage")
        return (msg or "").strip()
    except Exception:
        return ""


def assert_any_validation_evidence(page: Page, selector: str) -> None:
    """断言存在验证证据"""
    msg = get_validation_message(page, selector)
    if msg:
        return
    if has_any_error_ui(page):
        return
    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None and (400 <= resp.status < 500):
        return
    raise AssertionError("no validation evidence observed")


# Toast / Notification 选择器
# 该项目使用 Sonner-style notifications: <div role="region"> > <ol> > <li>
TOAST_SELECTORS = (
    "[role='region'][aria-label*='Notification'] li, "
    ".sonner-toast, [data-sonner-toast], "
    "[role='alert'], .toast"
)


def wait_for_toast(page: Page, timeout_ms: int = 5000) -> None:
    """等待 toast 出现"""
    try:
        page.wait_for_selector(
            TOAST_SELECTORS,
            state="visible",
            timeout=timeout_ms
        )
    except Exception:
        pass


def get_toast_text(page: Page) -> str:
    """获取 toast 文本"""
    try:
        toast = page.locator(TOAST_SELECTORS).first
        if toast.is_visible(timeout=1000):
            return (toast.inner_text(timeout=2000) or "").strip()
    except Exception:
        pass
    return ""


def assert_toast_contains_any(page: Page, needles: list[str]) -> None:
    """断言 toast 包含指定文本"""
    wait_for_toast(page, timeout_ms=3000)
    text = get_toast_text(page)
    assert any((n or "") in text for n in (needles or [])), f"toast not matched. want any={needles} got={text!r}"


def has_any_error_ui(page: Page) -> bool:
    """检查是否有错误 UI"""
    for sel in ERROR_SELECTORS:
        try:
            if page.is_visible(sel, timeout=500):
                return True
        except Exception:
            continue
    return False


def snapshot_inputs(page: Page, rules: list[dict]) -> Dict[str, str]:
    """快照输入框的值"""
    snap: Dict[str, str] = dict()
    for r in rules:
        sel = r.get("selector") or ""
        if not sel:
            continue
        if page.locator(sel).count() == 0:
            continue
        try:
            snap[sel] = page.input_value(sel)
        except Exception:
            continue
    return snap


def restore_inputs(page: Page, snap: Dict[str, str]) -> None:
    """恢复输入框的值"""
    for sel, val in snap.items():
        try:
            if page.locator(sel).count() == 0:
                continue
            page.fill(sel, val)
        except Exception:
            continue


def step_shot(page_obj, name: str, *, full_page: bool = True) -> None:
    """关键步骤截图（默认全页截图，确保 toast 等浮层也能被捕获）"""
    try:
        screenshot = page_obj.page.screenshot(full_page=full_page)
        allure.attach(screenshot, name, allure.attachment_type.PNG)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# 角色清理
# ═══════════════════════════════════════════════════════════════
#
# 约定：凡在用例中创建了 role 的测试，必须在用例末尾（try/finally 的 finally）
# 中调用 delete_test_role 清理该 role，避免产生垃圾数据。不创建新 role 的用例
# （如仅打开/关闭对话框、或提交重复名等）无需清理。
#

def delete_test_role(page_obj, role_name: str) -> None:
    """
    删除测试角色（通过 API）
    
    Args:
        page_obj: AdminRolesPage 实例
        role_name: 角色名称
    """
    try:
        success = page_obj.delete_role_by_name(role_name)
        if success:
            logger.info(f"成功删除测试角色: {role_name}")
        else:
            logger.warning(f"删除测试角色失败或角色不存在: {role_name}")
    except Exception as e:
        logger.warning(f"删除测试角色时出错: {role_name}, 错误: {e}")


def cleanup_test_roles(page_obj, role_names: list) -> None:
    """
    批量清理测试角色
    
    Args:
        page_obj: AdminRolesPage 实例
        role_names: 要清理的角色名称列表
    """
    if not role_names:
        logger.info("没有需要清理的角色")
        return
    
    logger.info(f"开始清理 {len(role_names)} 个测试角色")
    for role_name in role_names:
        try:
            delete_test_role(page_obj, role_name)
        except Exception as e:
            logger.warning(f"清理角色 {role_name} 时出错: {e}")
    logger.info("测试角色清理完成")

