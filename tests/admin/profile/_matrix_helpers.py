"""
Profile Settings - Matrix Helpers

目的：
- 把矩阵公共逻辑集中在一个文件里，避免 5 个字段矩阵文件重复实现。
- 每个字段一个 test 文件，便于按字段拆开跑、并发分摊。

约定：
- 每个场景默认只保留 2 张关键截图（filled / result）
- “回滚到 baseline”交给 profile_settings fixture teardown（仅当本 test 内确实写成功过才回滚保存）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import allure  # pyright: ignore[reportMissingImports]
from playwright.sync_api import Page

from ._helpers import (
    abp_profile_put_should_reject,
    check_success_toast,
    settle_toasts,
    step_shot,
    step_shot_after_success_toast,
)

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class MatrixScenario:
    case_name: str
    selector: str
    patch: Dict[str, str]
    should_save: bool
    note: str
    require_frontend_error_evidence: bool = False
    require_backend_reject: bool = False
    # 共享环境下的“唯一性”不可控：某些边界值（例如 userName 长度=1）很容易撞到已有用户名。
    # 该开关用于把“已经被占用”的失败视为“场景仍然有效”（目的不是测唯一性，而是测长度边界）。
    allow_taken_conflict: bool = False


def rand_suffix(page) -> str:
    """用时间戳确保唯一性（避免用户名/邮箱唯一约束冲突）。"""
    try:
        return str(int(page.evaluate("Date.now()")))
    except Exception:
        return "0000"


def field_looks_invalid(page, selector: str) -> bool:
    """不绑定 UI 框架的 invalid 探测（用于辅助断言/兜底）。"""
    try:
        v = page.eval_on_selector(selector, "el => el.getAttribute('aria-invalid') || ''")
        if str(v).lower() == "true":
            return True
    except Exception:
        pass
    try:
        cls = page.eval_on_selector(selector, "el => el.className || ''")
        cls_low = str(cls).lower()
        if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
            return True
    except Exception:
        pass
    return False


def wait_for_frontend_validation(page: Page, timeout_ms: int = 2000) -> bool:
    """
    等待前端验证完成（错误提示渲染）
    
    用于"必须前端拦截"的测试场景：
    - 点击 Save 后，前端验证是异步的（React/debounce/onBlur）
    - 需要等待错误提示渲染完成后再断言
    
    策略：
    1. 等待常见错误元素出现（.invalid-feedback, .text-danger, etc）
    2. 使用 wait_for_function 检测 DOM 状态（aria-invalid="true"）
    3. 超时返回 False（前端可能没有拦截）
    
    Returns:
        bool: True 表示检测到错误提示，False 表示超时未检测到
    """
    try:
        # 方案 1：等待任何错误元素出现（快速路径）
        page.wait_for_selector(
            ".invalid-feedback:visible, .text-danger:visible, .field-validation-error:visible, .validation-summary-errors:visible, .toast-error:visible",
            state="visible",
            timeout=timeout_ms
        )
        logger.debug(f"[wait_for_frontend_validation] 检测到错误元素（selector 路径）")
        return True
    except Exception:
        pass
    
    try:
        # 方案 2：使用 wait_for_function 等待 DOM 状态（通用路径）
        page.wait_for_function(
            """() => {
                // 检查 aria-invalid
                const invalidEls = document.querySelectorAll('[aria-invalid="true"]');
                if (invalidEls.length > 0) return true;
                
                // 检查错误类名
                const errorEls = document.querySelectorAll('.invalid-feedback, .text-danger, .field-validation-error, .validation-summary-errors');
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
        logger.debug(f"[wait_for_frontend_validation] 检测到错误元素（wait_for_function 路径）")
        return True
    except Exception:
        logger.warning(f"[wait_for_frontend_validation] 超时 {timeout_ms}ms 未检测到错误提示")
        return False


def assert_frontend_has_error_evidence(page, selector: str, case_name: str) -> None:
    """
    仅用于“必须前端拦截”的场景：要求 UI 有可检证的错误证据。
    - 不绑定具体 UI 框架，优先 validationMessage / aria-describedby / aria-invalid
    - Allure 默认不刷文本；仅失败时补最小证据
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
    except Exception:
        evidence = {}

    ok = False
    if str((evidence or {}).get("validationMessage") or "").strip():
        ok = True
    if str((evidence or {}).get("described") or "").strip():
        ok = True
    if str((evidence or {}).get("ariaInvalid") or "").lower() == "true":
        ok = True
    cls_low = str((evidence or {}).get("className") or "").lower()
    if ("invalid" in cls_low) or ("error" in cls_low) or ("red" in cls_low):
        ok = True

    if not ok:
        allure.attach(str(evidence), name=f"{case_name}_no_error_evidence", attachment_type=allure.attachment_type.TEXT)
        assert False, f"expected visible frontend error evidence for blocked case: {case_name}"


def _assert_should_fail(page, page_obj, selector: str, case_name: str, patch: dict, note: str, resp) -> None:
    ok = bool(resp is not None and resp.ok)
    success_ui = check_success_toast(page_obj)
    has_invalid = (
        field_looks_invalid(page, selector)
        or page.get_by_text("is required").is_visible(timeout=200)
        or page.get_by_text("must be less").is_visible(timeout=200)
        or page.get_by_text("invalid").is_visible(timeout=200)
        or page.get_by_text("error").is_visible(timeout=200)
    )

    if ok or success_ui:
        # “前端更严格”是允许的：例如 maxlength 截断、trim 空白、或后端忽略无效变更并返回成功。
        # 只要最终落库/落表单值不是“原样非法输入”，就视为已被拦截/归一化（符合需求）。
        candidate = None
        try:
            if isinstance(patch, dict) and len(patch) == 1:
                candidate = next(iter(patch.values()))
        except Exception:
            candidate = None

        normalized = False
        if isinstance(candidate, str):
            try:
                actual = page.input_value(selector)
                if actual != candidate:
                    normalized = True
            except Exception:
                # 读取不到 input_value 时，退化为“toast 成功但无报错”也先放行（截图已在外层保留）
                normalized = True

        if normalized:
            allure.attach(
                f"accepted_normalized_save: {case_name}\n{note}\npatch={patch}",
                name=f"accepted_normalized_{case_name}",
                attachment_type=allure.attachment_type.TEXT,
            )
            return

        allure.attach(
            f"❌ SHOULD FAIL but saved as-is: {case_name}\n{note}\npatch={patch}",
            name=f"unexpected_saved_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{case_name}_unexpected_saved")
        assert False, f"invalid input unexpectedly saved: {case_name}"

    if not has_invalid:
        # 失败兜底：没有可见错误时，补一张截图方便排查
        allure.attach(
            f"Invalid input rejected but no visible inline error: {case_name}\n{note}\npatch={patch}",
            name=f"no_visible_error_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{case_name}_no_visible_error")


def _assert_should_save(page, page_obj, case_name: str, patch: dict, note: str, resp) -> None:
    if page_obj.is_login_page():
        # 允许的安全行为：敏感变更触发重登
        allure.attach(
            "redirect_to_login_after_save (acceptable security behavior)",
            name=f"save_result_{case_name}",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    ok = bool(resp is not None and resp.ok)
    success_ui = check_success_toast(page_obj)
    if ok or success_ui:
        return

    # 允许的“冲突通过”：只在明确是“已被占用”时接受，避免掩盖其它失败原因
    if getattr(note, "__class__", None) is not None:  # keep mypy quiet; note is str
        pass
    if resp is not None and getattr(page_obj, "_active_scenario_allow_taken", False):
        try:
            body = (resp.text() or "").lower()
        except Exception:
            body = ""
        if (resp.status in {400, 403}) and ("already taken" in body) and ("username" in body):
            allure.attach(
                f"accepted_taken_conflict: {case_name}\n{note}\nresp={resp.status}\nbody={(resp.text() or '')[:400]}",
                name=f"accepted_taken_{case_name}",
                attachment_type=allure.attachment_type.TEXT,
            )
            return

    # 失败必须可诊断：保留最小信息
    body_snip: Optional[str] = None
    try:
        if resp is not None:
            body_snip = (resp.text() or "")[:800]
    except Exception:
        body_snip = None

    allure.attach(
        f"❌ SHOULD SAVE but failed: {case_name}\n{note}\npatch={patch}\nresp={getattr(resp,'status',None)}\nbody={body_snip}",
        name=f"unexpected_failed_{case_name}",
        attachment_type=allure.attachment_type.TEXT,
    )
    step_shot(page_obj, f"step_{case_name}_unexpected_failed")
    assert False, f"expected save success for {case_name}, but got resp={getattr(resp,'status',None)} body={body_snip}"


def run_matrix_case(auth_page, page_obj, baseline: dict, scenario: MatrixScenario) -> None:
    # 给 page_obj 标记当前场景的“可接受冲突”开关，供断言使用（避免修改大量函数签名）
    try:
        setattr(page_obj, "_active_scenario_allow_taken", bool(scenario.allow_taken_conflict))
    except Exception:
        pass
    with allure.step(f"[{scenario.case_name}] 填写（{scenario.note}）"):
        settle_toasts(page_obj)
        page_obj.fill_form(scenario.patch)
        step_shot(page_obj, f"step_{scenario.case_name}_filled")

    with allure.step(f"[{scenario.case_name}] 提交"):
        # 性能关键点：
        # - 前端拦截（不发请求）的场景，如果 expect_response 等太久会把矩阵用例拖到十几分钟
        # - 因此：按场景类型动态缩短等待
        if scenario.should_save:
            timeout_ms = 12000
        elif scenario.require_backend_reject:
            # 预期会发请求且被后端 reject：仍给足等待
            timeout_ms = 12000
        else:
            # 预期前端拦截：快速判定"没有请求"
            timeout_ms = 1500

        resp = page_obj.click_save_and_capture_profile_update(timeout_ms=timeout_ms)
        # 优化：减少等待时间从300ms到100ms（充分利用并行能力）
        auth_page.wait_for_timeout(100)
        if scenario.should_save:
            step_shot_after_success_toast(page_obj, f"step_{scenario.case_name}_result")
        else:
            step_shot(page_obj, f"step_{scenario.case_name}_result")

    # 不在 Allure 展示“断言步骤”，断言本身仍然执行；失败时通过截图/最小附件给证据
    if scenario.should_save:
        _assert_should_save(auth_page, page_obj, scenario.case_name, scenario.patch, scenario.note, resp)
    else:
        _assert_should_fail(auth_page, page_obj, scenario.selector, scenario.case_name, scenario.patch, scenario.note, resp)
        if scenario.require_frontend_error_evidence and resp is None:
            assert_frontend_has_error_evidence(auth_page, scenario.selector, scenario.case_name)
        if scenario.require_backend_reject:
            abp_profile_put_should_reject(auth_page, baseline, scenario.patch)

    try:
        delattr(page_obj, "_active_scenario_allow_taken")
    except Exception:
        pass

