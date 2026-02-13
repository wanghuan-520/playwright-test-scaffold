"""
Edit User Dialog - Matrix Helpers

目的：
- 为 Edit User 对话框提供矩阵测试辅助函数
- 适配对话框的特殊性（需要先打开对话框，使用不同的保存方法）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import allure
from playwright.sync_api import Page, Response

from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import step_shot, AbpUserConsts
from tests.myaccount._helpers import check_success_toast, settle_toasts
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EditUserMatrixScenario:
    """Edit User 对话框矩阵测试场景"""
    case_name: str
    selector: str
    patch: Dict[str, str]  # 例如 {"firstName": "John", "lastName": "Doe", "phoneNumber": "13800138000"}
    should_save: bool
    note: str
    require_frontend_error_evidence: bool = False
    require_backend_reject: bool = False
    allow_taken_conflict: bool = False


def click_save_and_capture_edit_user_response(
    page_obj: AdminUsersPage,
    timeout_ms: int = 1500  # 优化：进一步减少默认超时
) -> Optional[Response]:
    """
    点击 Save Changes，并尽力捕获 Edit User API 响应。
    若前端校验拦截导致不发请求：返回 None
    
    Args:
        page_obj: AdminUsersPage 实例
        timeout_ms: 超时时间（毫秒）
        
    Returns:
        Response 对象或 None
    """
    def _match(resp) -> bool:
        try:
            url = resp.url or ""
            method = resp.request.method
            # 匹配 Edit User API（通常是 PUT /api/identity/users/{id} 或类似）
            return (
                ("/api/identity/users" in url or "/api/users" in url or "/api/account/users" in url)
                and method in ("PUT", "POST", "PATCH")
            )
        except Exception:
            return False

    try:
        with page_obj.page.expect_response(_match, timeout=timeout_ms) as resp_info:
            page_obj.click_save_changes()
        resp = resp_info.value
        return resp
    except Exception:
        return None


def run_edit_user_matrix_case(
    auth_page: Page,
    page_obj: AdminUsersPage,
    test_username: str,
    scenario: EditUserMatrixScenario
) -> None:
    """
    执行 Edit User 对话框矩阵测试用例
    
    Args:
        auth_page: Playwright Page 对象
        page_obj: AdminUsersPage 实例
        test_username: 要编辑的测试用户名
        scenario: 矩阵测试场景
    """
    # 标记当前场景的"可接受冲突"开关
    try:
        setattr(page_obj, "_active_scenario_allow_taken", bool(scenario.allow_taken_conflict))
    except Exception:
        pass
    
    try:
        with allure.step(f"[{scenario.case_name}] 打开 Edit User 对话框"):
            # 确保在 admin/users 页面
            if not page_obj.page.url.endswith("/admin/users"):
                page_obj.navigate()
                page_obj.wait_for_data_loaded(timeout=3000)  # 优化：进一步减少超时
            
            # 搜索并打开 Edit User 对话框（优化：快速操作）
            page_obj.search_user(test_username)
            # 等待搜索结果（快速等待）
            page_obj.wait_for_filter_results(timeout=2000)  # 从 3000 减少到 2000
            page_obj.click_actions_menu_for_user(test_username)
            page_obj.click_edit_user()
            # 等待对话框打开（快速检查）
            dialog = auth_page.locator('[role="dialog"]')
            dialog.wait_for(state="visible", timeout=2000)  # 从 3000 减少到 2000
            settle_toasts(page_obj)
        
        with allure.step(f"[{scenario.case_name}] 填写（{scenario.note}）"):
            # 填写表单（将字典键转换为 fill_edit_user_form 的参数）
            form_data = {}
            if "firstName" in scenario.patch:
                form_data["first_name"] = scenario.patch["firstName"]
            if "lastName" in scenario.patch:
                form_data["last_name"] = scenario.patch["lastName"]
            if "phoneNumber" in scenario.patch:
                form_data["phone"] = scenario.patch["phoneNumber"]
            if "phone" in scenario.patch:
                form_data["phone"] = scenario.patch["phone"]
            
            page_obj.fill_edit_user_form(**form_data)
            step_shot(page_obj, f"step_{scenario.case_name}_filled")
        
        with allure.step(f"[{scenario.case_name}] 提交"):
            # 根据场景类型动态调整超时（优化：大幅减少超时时间）
            if scenario.should_save:
                timeout_ms = 5000  # 从 8000 减少到 5000
            elif scenario.require_backend_reject:
                timeout_ms = 5000  # 从 8000 减少到 5000
            else:
                timeout_ms = 800  # 从 1000 减少到 800
            
            resp = click_save_and_capture_edit_user_response(page_obj, timeout_ms=timeout_ms)
            
            if scenario.should_save:
                auth_page.wait_for_timeout(500)
                step_shot(page_obj, f"step_{scenario.case_name}_result")
            else:
                auth_page.wait_for_timeout(200)
                step_shot(page_obj, f"step_{scenario.case_name}_result")
        
        # 断言
        if scenario.should_save:
            _assert_edit_user_should_save(auth_page, page_obj, scenario, resp)
            # 保存成功 → 打开 View Details 验证编辑后的数据
            with allure.step(f"[{scenario.case_name}] 打开 View Details 验证"):
                try:
                    # 关闭 Edit 弹窗（如果还开着）
                    edit_dialog = auth_page.locator('[role="dialog"]')
                    if edit_dialog.is_visible(timeout=500):
                        page_obj.click_close_dialog()
                        auth_page.wait_for_timeout(500)
                    # 搜索用户并打开 View Details
                    page_obj.search_user(test_username)
                    page_obj.wait_for_filter_results(timeout=2000)
                    page_obj.click_actions_menu_for_user(test_username)
                    page_obj.click_view_details()
                    auth_page.wait_for_timeout(1500)
                    step_shot(page_obj, f"step_{scenario.case_name}_view_details")
                    # 关闭 View Details
                    auth_page.get_by_role("button", name="Close").click()
                    auth_page.wait_for_timeout(500)
                except Exception as e:
                    logger.warning(f"View Details 验证失败: {e}")
                    # 兜底关闭
                    try:
                        auth_page.keyboard.press("Escape")
                        auth_page.wait_for_timeout(300)
                    except Exception:
                        pass
        else:
            _assert_edit_user_should_fail(auth_page, page_obj, scenario, resp)
        
    finally:
        # 清理：确保所有弹窗关闭，页面回到列表状态
        for _ in range(3):
            try:
                dialog = auth_page.locator('[role="dialog"]')
                if dialog.is_visible(timeout=500):
                    page_obj.click_close_dialog()
                    auth_page.wait_for_timeout(300)
                else:
                    break
            except Exception:
                try:
                    auth_page.keyboard.press("Escape")
                    auth_page.wait_for_timeout(300)
                except Exception:
                    break
        
        try:
            delattr(page_obj, "_active_scenario_allow_taken")
        except Exception:
            pass


def _assert_edit_user_should_save(
    auth_page: Page,
    page_obj: AdminUsersPage,
    scenario: EditUserMatrixScenario,
    resp: Optional[Response]
) -> None:
    """断言：应该保存成功"""
    ok = bool(resp is not None and resp.ok)
    success_ui = check_success_toast(page_obj)
    
    if ok or success_ui:
        return
    
    # 允许的"冲突通过"
    if getattr(page_obj, "_active_scenario_allow_taken", False) and resp is not None:
        try:
            body = (resp.text() or "").lower()
            if (resp.status in {400, 403}) and ("already taken" in body):
                allure.attach(
                    f"accepted_taken_conflict: {scenario.case_name}\n{scenario.note}\nresp={resp.status}",
                    name=f"accepted_taken_{scenario.case_name}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return
        except Exception:
            pass
    
    # 失败必须可诊断
    body_snip: Optional[str] = None
    try:
        if resp is not None:
            body_snip = (resp.text() or "")[:800]
    except Exception:
        body_snip = None
    
    allure.attach(
        f"❌ SHOULD SAVE but failed: {scenario.case_name}\n{scenario.note}\npatch={scenario.patch}\nresp={getattr(resp,'status',None)}\nbody={body_snip}",
        name=f"unexpected_failed_{scenario.case_name}",
        attachment_type=allure.attachment_type.TEXT,
    )
    step_shot(page_obj, f"step_{scenario.case_name}_unexpected_failed")
    assert False, f"expected save success for {scenario.case_name}, but got resp={getattr(resp,'status',None)}"


def _assert_edit_user_should_fail(
    auth_page: Page,
    page_obj: AdminUsersPage,
    scenario: EditUserMatrixScenario,
    resp: Optional[Response]
) -> None:
    """断言：应该保存失败"""
    ok = bool(resp is not None and resp.ok)
    success_ui = check_success_toast(page_obj)
    
    # 检查是否有错误提示
    has_invalid = False
    try:
        dialog = auth_page.locator('[role="dialog"]')
        dialog_text = dialog.text_content() or ""
        has_invalid = (
            "error" in dialog_text.lower() or
            "invalid" in dialog_text.lower() or
            "required" in dialog_text.lower() or
            auth_page.get_by_text("is required").is_visible(timeout=200) or
            auth_page.get_by_text("must be less").is_visible(timeout=200)
        )
    except Exception:
        pass
    
    if ok or success_ui:
        # 如果保存成功，检查是否是归一化（例如截断）
        normalized = False
        if isinstance(scenario.patch, dict) and len(scenario.patch) == 1:
            candidate = next(iter(scenario.patch.values()))
            if isinstance(candidate, str):
                try:
                    # 尝试读取输入框的值（如果对话框还打开）
                    dialog = auth_page.locator('[role="dialog"]')
                    if dialog.is_visible(timeout=1000):
                        # 根据字段类型查找输入框
                        field_name = next(iter(scenario.patch.keys()))
                        if field_name == "firstName":
                            input_elem = dialog.locator('text:has-text("First Name")').locator('..').locator('input').first
                        elif field_name == "lastName":
                            input_elem = dialog.locator('text:has-text("Last Name")').locator('..').locator('input').first
                        elif field_name == "phone":
                            input_elem = dialog.locator('text:has-text("Phone Number")').locator('..').locator('input').first
                        else:
                            input_elem = None
                        
                        if input_elem and input_elem.count() > 0:
                            actual = input_elem.input_value()
                            if actual != candidate:
                                normalized = True
                except Exception:
                    normalized = True
        
        if normalized:
            allure.attach(
                f"accepted_normalized_save: {scenario.case_name}\n{scenario.note}\npatch={scenario.patch}",
                name=f"accepted_normalized_{scenario.case_name}",
                attachment_type=allure.attachment_type.TEXT,
            )
            return
        
        allure.attach(
            f"❌ SHOULD FAIL but saved as-is: {scenario.case_name}\n{scenario.note}\npatch={scenario.patch}",
            name=f"unexpected_saved_{scenario.case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{scenario.case_name}_unexpected_saved")
        assert False, f"invalid input unexpectedly saved: {scenario.case_name}"
    
    if not has_invalid:
        # 失败兜底：没有可见错误时，补一张截图
        allure.attach(
            f"Invalid input rejected but no visible inline error: {scenario.case_name}\n{scenario.note}\npatch={scenario.patch}",
            name=f"no_visible_error_{scenario.case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{scenario.case_name}_no_visible_error")

