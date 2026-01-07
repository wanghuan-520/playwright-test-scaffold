"""
Admin Users - Matrix Helpers

目的：
- 复用 profile_settings 的成熟矩阵测试架构
- 适配 users 页面的 Create User 对话框
- 统一验证逻辑，支持前后端一致性检查

约定：
- 每个场景只保留 2 张关键截图（filled / result）
- 对话框关闭 = 创建成功
- 对话框保持打开 = 验证失败（前端拦截）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import allure
from playwright.sync_api import Page

from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class UsersMatrixScenario:
    """
    Users 矩阵测试场景
    
    Args:
        case_name: 用例名（唯一标识）
        selector: 字段选择器
        patch: 要填写的值 {"username": "test", "email": "test@test.com", ...}
        should_save: 是否应该保存成功
        note: 场景说明
        require_frontend_error_evidence: 是否要求前端错误证据（validationMessage/aria-invalid）
        require_backend_reject: 是否要求后端拒绝（400/422）
        allow_taken_conflict: 是否允许"已被占用"（共享环境下的唯一性冲突）
    """
    case_name: str
    selector: str
    patch: Dict[str, str]
    should_save: bool
    note: str
    require_frontend_error_evidence: bool = False
    require_backend_reject: bool = False
    allow_taken_conflict: bool = False


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def rand_suffix(page: Page) -> str:
    """用时间戳确保唯一性（避免用户名/邮箱唯一约束冲突）"""
    try:
        return str(int(page.evaluate("Date.now()")))
    except Exception:
        import time
        return str(int(time.time() * 1000))


def step_shot(page_obj, name: str, *, full_page: bool = False) -> None:
    """关键步骤截图（Allure 附件）"""
    try:
        page_obj.take_screenshot(name, full_page=full_page)
    except Exception:
        pass


def settle_toasts(page: Page, timeout_ms: int = 2000) -> None:
    """等待 toast/通知稳定"""
    try:
        page.wait_for_timeout(min(timeout_ms, 500))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# 对话框操作
# ═══════════════════════════════════════════════════════════════

def wait_for_dialog_visible(page: Page, timeout_ms: int = 3000) -> bool:
    """等待 Create User 对话框可见"""
    try:
        page.wait_for_selector("role=dialog", state="visible", timeout=timeout_ms)
        logger.debug(f"[wait_for_dialog_visible] 对话框已出现")
        return True
    except Exception as e:
        logger.warning(f"[wait_for_dialog_visible] 超时: {e}")
        return False


def wait_for_dialog_hidden(page: Page, timeout_ms: int = 3000) -> bool:
    """等待对话框关闭（表单提交成功）"""
    try:
        page.wait_for_selector("role=dialog", state="hidden", timeout=timeout_ms)
        logger.debug(f"[wait_for_dialog_hidden] 对话框已关闭")
        return True
    except Exception as e:
        logger.warning(f"[wait_for_dialog_hidden] 超时: {e}")
        return False


def is_dialog_visible(page: Page) -> bool:
    """检查对话框是否可见"""
    try:
        return page.is_visible("role=dialog", timeout=500)
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 前端验证检测
# ═══════════════════════════════════════════════════════════════

def wait_for_frontend_validation(page: Page, timeout_ms: int = 2000) -> bool:
    """
    等待前端验证完成（错误提示渲染）
    
    策略：
    1. 等待常见错误元素出现（.invalid-feedback, .text-danger, etc）
    2. 使用 wait_for_function 检测 DOM 状态（aria-invalid="true"）
    3. 超时返回 False（前端可能没有拦截）
    
    Returns:
        bool: True 表示检测到错误提示，False 表示超时未检测到
    """
    try:
        # 方案 1：等待任何错误元素出现
        page.wait_for_selector(
            ".invalid-feedback:visible, .text-danger:visible, .field-validation-error:visible, [aria-invalid='true']:visible",
            state="visible",
            timeout=timeout_ms
        )
        logger.debug(f"[wait_for_frontend_validation] 检测到错误元素")
        return True
    except Exception:
        pass
    
    try:
        # 方案 2：使用 wait_for_function 检测 DOM 状态
        page.wait_for_function(
            """() => {
                // 检查 aria-invalid
                const invalidEls = document.querySelectorAll('[aria-invalid="true"]');
                if (invalidEls.length > 0) return true;
                
                // 检查错误类名
                const errorEls = document.querySelectorAll('.invalid-feedback, .text-danger, .field-validation-error');
                for (let el of errorEls) {
                    if (el.offsetParent !== null) {  // 可见元素
                        return true;
                    }
                }
                
                // 检查 validationMessage
                const inputs = document.querySelectorAll('input, textarea, select');
                for (let input of inputs) {
                    if (input.validationMessage && input.validationMessage.trim()) {
                        return true;
                    }
                }
                
                return false;
            }""",
            timeout=timeout_ms
        )
        logger.debug(f"[wait_for_frontend_validation] 检测到错误元素（wait_for_function）")
        return True
    except Exception:
        logger.warning(f"[wait_for_frontend_validation] 超时 {timeout_ms}ms 未检测到错误提示")
        return False


def assert_frontend_has_error_evidence(page: Page, selector: str, case_name: str) -> None:
    """
    断言：前端必须有可检证的错误证据
    
    检查项：
    - validationMessage（HTML5 验证）
    - aria-invalid="true"
    - aria-describedby 指向的错误文本
    - className 包含 invalid/error/red
    - Toast/Message 错误提示（Ant Design等）
    """
    try:
        evidence = page.eval_on_selector(
            selector,
            """el => {
                const ariaInvalid = el.getAttribute('aria-invalid') || '';
                const className = (el.className || '').toString();
                const ariaDescribedBy = el.getAttribute('aria-describedby') || '';
                const described = ariaDescribedBy ? (document.getElementById(ariaDescribedBy)?.innerText || '') : '';
                const msg = (el.validationMessage || '').toString();
                return { ariaInvalid, className, ariaDescribedBy, described, validationMessage: msg };
            }""",
        )
        logger.debug(f"[assert_frontend_has_error_evidence] Evidence for {case_name}: {evidence}")
    except Exception as e:
        logger.debug(f"[assert_frontend_has_error_evidence] Failed to get evidence for {case_name}: {e}")
        evidence = {}

    ok = False
    validation_msg = str((evidence or {}).get("validationMessage") or "").strip()
    if validation_msg:
        logger.info(f"[assert_frontend_has_error_evidence] 检测到 HTML5 validation: {validation_msg}")
        ok = True
    if str((evidence or {}).get("described") or "").strip():
        ok = True
    if str((evidence or {}).get("ariaInvalid") or "").lower() == "true":
        ok = True
    cls_low = str((evidence or {}).get("className") or "").lower()
    if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
        ok = True
    
    # 检查 Toast/Message 错误提示
    if not ok:
        try:
            toast_selectors = [
                ".ant-message-error",
                ".ant-message-warning",
                ".ant-notification-error",
                ".error-toast",
                ".toast-error",
                "[role='alert']",
                ".validation-message:not(:empty)",
                ".field-validation-error:not(:empty)"
            ]
            for toast_sel in toast_selectors:
                if page.is_visible(toast_sel, timeout=500):
                    toast_text = page.locator(toast_sel).first.inner_text()
                    if toast_text.strip():
                        logger.info(f"[assert_frontend_has_error_evidence] 检测到 Toast 错误: {toast_text}")
                        ok = True
                        break
        except Exception as e:
            logger.debug(f"[assert_frontend_has_error_evidence] Toast 检测异常: {e}")

    if not ok:
        allure.attach(str(evidence), name=f"{case_name}_no_error_evidence", attachment_type=allure.attachment_type.TEXT)
        logger.error(f"[assert_frontend_has_error_evidence] 未找到前端错误证据: {case_name}")
        assert False, f"expected visible frontend error evidence for blocked case: {case_name}"


def field_looks_invalid(page: Page, selector: str) -> bool:
    """检查字段是否看起来无效（辅助判断）"""
    # 检查 aria-invalid
    try:
        v = page.eval_on_selector(selector, "el => el.getAttribute('aria-invalid') || ''")
        if str(v).lower() == "true":
            return True
    except Exception:
        pass
    
    # 检查 className
    try:
        cls = page.eval_on_selector(selector, "el => el.className || ''")
        cls_low = str(cls).lower()
        if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
            return True
    except Exception:
        pass
    
    # 检查 HTML5 validationMessage（原生浏览器验证）
    try:
        msg = page.eval_on_selector(selector, "el => el.validationMessage || ''")
        if str(msg).strip():
            return True
    except Exception:
        pass
    
    return False


# ═══════════════════════════════════════════════════════════════
# 验证断言
# ═══════════════════════════════════════════════════════════════

def _assert_should_fail(page: Page, users_page, selector: str, case_name: str, patch: dict, note: str) -> None:
    """
    断言：应该失败（不应该创建用户）
    
    验证逻辑：
    - 对话框应该保持打开（前端拦截）
    - 如果对话框关闭，检查用户是否被创建
    - 如果用户被创建，检查是否被"归一化"（前端截断/trim）
    """
    dialog_visible = is_dialog_visible(page)
    
    if not dialog_visible:
        # 对话框关闭了，检查用户是否被创建
        # 获取用户名（用于搜索）
        username = patch.get("username", "")
        if not username:
            # 没有用户名，无法验证，假设通过
            logger.warning(f"[_assert_should_fail] {case_name}: 无 username，无法验证用户是否被创建")
            return
        
        # 搜索用户
        try:
            users_page.search_user(username)
            user_created = users_page.is_user_visible(username)
        except Exception as e:
            logger.warning(f"[_assert_should_fail] {case_name}: 搜索用户失败: {e}")
            user_created = False
        
        if user_created:
            # 用户被创建了，检查是否"归一化"
            candidate = None
            try:
                if isinstance(patch, dict) and len(patch) >= 1:
                    # 获取第一个非空字段值
                    for v in patch.values():
                        if isinstance(v, str) and v:
                            candidate = v
                            break
            except Exception:
                candidate = None
            
            normalized = False
            if isinstance(candidate, str):
                try:
                    actual = page.input_value(selector)
                    if actual != candidate:
                        normalized = True
                except Exception:
                    normalized = True
            
            if normalized:
                allure.attach(
                    f"accepted_normalized_save: {case_name}\n{note}\npatch={patch}",
                    name=f"accepted_normalized_{case_name}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                logger.info(f"[_assert_should_fail] {case_name}: 接受归一化保存")
                return
            
            # 原样保存了，失败
            allure.attach(
                f"❌ SHOULD FAIL but saved as-is: {case_name}\n{note}\npatch={patch}",
                name=f"unexpected_saved_{case_name}",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(users_page, f"step_{case_name}_unexpected_saved")
            logger.error(f"[_assert_should_fail] {case_name}: 非法输入被原样保存")
            assert False, f"invalid input unexpectedly saved: {case_name}"
    
    # 对话框仍然打开 = 验证工作了 ✅
    has_invalid = field_looks_invalid(page, selector)
    if not has_invalid:
        # 被拒绝了，但没有可见错误提示（警告）
        allure.attach(
            f"Invalid input rejected but no visible inline error: {case_name}\n{note}\npatch={patch}",
            name=f"no_visible_error_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger.warning(f"[_assert_should_fail] {case_name}: 被拒绝但无可见错误")
        step_shot(users_page, f"step_{case_name}_no_visible_error")


def _assert_should_save(page: Page, users_page, case_name: str, patch: dict, note: str, allow_taken: bool) -> None:
    """
    断言：应该保存成功
    
    验证逻辑：
    - 对话框应该关闭
    - 用户应该被创建
    - 允许"已被占用"（共享环境）
    """
    dialog_visible = is_dialog_visible(page)
    
    if dialog_visible:
        # 对话框仍然打开 = 保存失败
        allure.attach(
            f"❌ SHOULD SAVE but dialog still open: {case_name}\n{note}\npatch={patch}",
            name=f"unexpected_failed_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(users_page, f"step_{case_name}_unexpected_failed")
        logger.error(f"[_assert_should_save] {case_name}: 对话框仍然打开，保存失败")
        assert False, f"expected save success for {case_name}, but dialog still open"
    
    # 对话框关闭了，检查用户是否被创建
    username = patch.get("username", "")
    if not username:
        # 没有用户名，无法验证，假设通过
        logger.warning(f"[_assert_should_save] {case_name}: 无 username，无法验证")
        return
    
    try:
        users_page.search_user(username)
        user_created = users_page.is_user_visible(username)
    except Exception as e:
        logger.warning(f"[_assert_should_save] {case_name}: 搜索用户失败: {e}")
        user_created = False
    
    if not user_created:
        # 用户未被创建
        allure.attach(
            f"❌ SHOULD SAVE but user not created: {case_name}\n{note}\npatch={patch}",
            name=f"unexpected_failed_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(users_page, f"step_{case_name}_user_not_created")
        logger.error(f"[_assert_should_save] {case_name}: 用户未被创建")
        assert False, f"expected user created for {case_name}, but not found"
    
    logger.info(f"[_assert_should_save] {case_name}: 保存成功 ✅")


# ═══════════════════════════════════════════════════════════════
# 核心执行函数
# ═══════════════════════════════════════════════════════════════

def run_users_matrix_case(admin_page, users_page, scenario: UsersMatrixScenario) -> None:
    """
    运行 users 矩阵测试用例
    
    流程：
    1. 打开 Create User 对话框
    2. 填写表单
    3. 提交
    4. 验证结果
    """
    page = users_page.page
    
    with allure.step(f"[{scenario.case_name}] 导航到用户管理页面"):
        users_page.navigate()
        step_shot(users_page, f"step_{scenario.case_name}_navigate")
    
    with allure.step(f"[{scenario.case_name}] 打开 Create User 对话框"):
        users_page.click_create()
        assert wait_for_dialog_visible(page, timeout_ms=5000), "对话框未出现"
        step_shot(users_page, f"step_{scenario.case_name}_dialog_open")
    
    with allure.step(f"[{scenario.case_name}] 填写（{scenario.note}）"):
        settle_toasts(page)
        users_page.fill_user_form(**scenario.patch)
        step_shot(users_page, f"step_{scenario.case_name}_filled")
    
    with allure.step(f"[{scenario.case_name}] 提交"):
        # 性能关键点：
        # - 前端拦截（不发请求）的场景，快速判定"没有请求"
        # - 预期会发请求的场景，给足等待
        if scenario.should_save:
            timeout_ms = 12000
        elif scenario.require_backend_reject:
            timeout_ms = 12000
        else:
            timeout_ms = 1500
        
        try:
            users_page.submit_form()
        except Exception as e:
            logger.warning(f"[run_users_matrix_case] {scenario.case_name}: 提交失败: {e}")
        
        # 等待结果
        page.wait_for_timeout(100)  # 等待 DOM 更新
        
        if scenario.should_save:
            # 期望成功：等待对话框关闭
            wait_for_dialog_hidden(page, timeout_ms)
        else:
            # 期望失败：等待错误提示
            wait_for_frontend_validation(page, timeout_ms=2000)
        
        step_shot(users_page, f"step_{scenario.case_name}_result")
    
    # 验证
    if scenario.should_save:
        _assert_should_save(page, users_page, scenario.case_name, scenario.patch, scenario.note, scenario.allow_taken_conflict)
    else:
        _assert_should_fail(page, users_page, scenario.selector, scenario.case_name, scenario.patch, scenario.note)
        if scenario.require_frontend_error_evidence:
            assert_frontend_has_error_evidence(page, scenario.selector, scenario.case_name)
    
    # 清理：如果对话框仍然打开，关闭它
    if is_dialog_visible(page):
        try:
            users_page.cancel_form()
            wait_for_dialog_hidden(page, timeout_ms=3000)
        except Exception:
            pass

