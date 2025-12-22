# ═══════════════════════════════════════════════════════════════
# Profile Settings (Personal Settings) - P0
# ═══════════════════════════════════════════════════════════════
"""
P0：主链路 + 必填字段逐条校验（字段维度）。

强制：
- 每个关键步骤都要截图（allure.step + take_screenshot）

注意：
- 本目录使用 profile_settings fixture 做 baseline 修正与 teardown 回滚，避免状态泄漏。
"""

import pytest
import allure

from utils.logger import TestLogger
from ._helpers import attach_rule_source_note, now_suffix, step_shot, step_shot_after_success_toast, settle_toasts

# P0 加速：复用同一个已登录 page/context，避免每条用例重复 new_context + navigate
# 开关：P0_SHARED_PAGE=1（默认关闭，保持最强隔离）
import os
from typing import Dict, Tuple
from playwright.sync_api import Page
from pages.personal_settings_page import PersonalSettingsPage


def _diff_profile_values(a: Dict[str, str], b: Dict[str, str]) -> Dict[str, Tuple[str, str]]:
    keys = ["userName", "name", "surname", "email", "phoneNumber"]
    return {k: ((a.get(k) or ""), (b.get(k) or "")) for k in keys if (a.get(k) or "") != (b.get(k) or "")}


@pytest.fixture(scope="module")
def profile_settings_shared(browser, ensure_auth_storage_state, auth_storage_state_path: str):
    """
    P0 专用共享 fixture：
    - module 级复用 context/page（大幅减少启动/导航开销）
    - 仍保持“每条用例前后按需回滚”，避免状态污染
    """
    if os.getenv("P0_SHARED_PAGE", "0") != "1":
        pytest.skip("P0_SHARED_PAGE is disabled")

    ctx = browser.new_context(
        ignore_https_errors=True,
        viewport={"width": 1920, "height": 1080},
        storage_state=auth_storage_state_path,
    )
    page = ctx.new_page()
    page_obj = PersonalSettingsPage(page)
    page_obj.navigate()

    # baseline：共享模式下只做一次 baseline 修正，后续用例前后回滚到它
    baseline = page_obj.read_form_values()
    yield page, page_obj, baseline
    try:
        ctx.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def profile_settings_p0(profile_settings, request):
    """
    兼容入口：
    - 默认：使用原 function-scope 的 profile_settings（最强隔离）
    - P0_SHARED_PAGE=1：使用 module-scope 的共享 page（更快）
    """
    if os.getenv("P0_SHARED_PAGE", "0") != "1":
        # 必须 yield，否则 pytest 会认为 fixture “没有产出值”
        yield profile_settings
        return

    shared = request.getfixturevalue("profile_settings_shared")
    page, page_obj, baseline = shared

    # 每条用例开始前：若不是 baseline，先按需回滚（避免上条失败污染）
    try:
        current = page_obj.read_form_values()
        diff = _diff_profile_values(current, baseline)
        if diff:
            settle_toasts(page_obj)
            page_obj.fill_form({k: baseline.get(k, "") for k in diff.keys()})
            resp = page_obj.click_save_and_capture_profile_update(timeout_ms=8000)
            # 若没有请求，也要确保值确实恢复
            after = page_obj.read_form_values()
            diff2 = _diff_profile_values(after, baseline)
            assert not diff2, f"shared baseline pre-restore failed: {diff2}"
    except Exception:
        # 兜底：重新导航一次，避免卡在异常 UI 状态
        page_obj.navigate()

    yield page, page_obj, baseline

    # 每条用例结束后：按需回滚（只在有 diff 时才保存）
    try:
        current = page_obj.read_form_values()
        diff = _diff_profile_values(current, baseline)
        if diff:
            settle_toasts(page_obj)
            page_obj.fill_form({k: baseline.get(k, "") for k in diff.keys()})
            resp = page_obj.click_save_and_capture_profile_update(timeout_ms=12000)
            after = page_obj.read_form_values()
            diff2 = _diff_profile_values(after, baseline)
            assert not diff2, f"shared teardown restore failed: {diff2}"
    except Exception:
        pass


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - 主流程")
@allure.description(
    """
测试点：
- 页面可正常打开（/admin/profile），不被重定向到登录页
- 核心控件可见：User name / Email / Save
- 证据：关键步骤截图（navigate / verify）
"""
)
def test_p0_profile_settings_page_load(profile_settings_p0):
    """P0: 页面加载 + 核心控件可见"""
    attach_rule_source_note()
    logger = TestLogger("test_p0_profile_settings_page_load")
    logger.start()

    auth_page, page_obj, _baseline = profile_settings_p0

    with allure.step("导航到 /admin/profile（Personal Settings）"):
        # profile_settings fixture 已完成导航
        step_shot(page_obj, "step_navigate")

    # 不在 Allure 展示“断言步骤”，仅保留截图证据；断言仍然执行
    assert not page_obj.is_login_page(), f"疑似未登录，current_url={auth_page.url}"
    step_shot(page_obj, "step_verify_not_login")

    assert page_obj.is_visible(page_obj.USERNAME_INPUT, timeout=3000)
    assert page_obj.is_visible(page_obj.EMAIL_INPUT, timeout=3000)
    assert page_obj.is_visible(page_obj.SAVE_BUTTON, timeout=3000)
    step_shot(page_obj, "step_verify_controls")

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - 主流程")
@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Profile Settings")
@allure.story("P0 - 主流程")
@allure.description(
    """
测试点：
- 一次性更新 5 个字段（userName/name/surname/email/phoneNumber）并保存成功（profileUpdate OK 或 Success toast）
- 不在用例内展示“回滚/断言步骤”，只保留关键证据截图
- 回滚策略：用例内只回填 UI；若本用例确实写成功过，fixture teardown 会按需回滚服务端到 baseline
"""
)
def test_p0_profile_settings_save_success(profile_settings_p0):
    """P0: 保存成功（happy path）；回滚交给 fixture teardown（避免重复保存耗时）"""
    attach_rule_source_note()
    logger = TestLogger("test_p0_profile_settings_save_success")
    logger.start()

    _page, page_obj, baseline = profile_settings_p0

    initial = baseline

    suffix = now_suffix()
    # 约束：
    # - userName/email 需要唯一（避免 “already taken”）
    # - phoneNumber <= 16
    new_values = {
        "userName": f"p0_{suffix}",
        "name": f"Auto_{suffix}",
        "surname": f"Run_{suffix}",
        "email": f"p0_{suffix}@t.com",
        "phoneNumber": (f"138{suffix}")[:11],
    }

    with allure.step("更新 5 个字段并点击 Save（期望成功）"):
        # 字段更新前截图：用于前后对比（证据链）
        step_shot(page_obj, "step_before_update")
        page_obj.fill_form(new_values)
        step_shot(page_obj, "step_fill_form")
        resp = page_obj.save_and_wait_profile_update(timeout_ms=20000)
        assert resp.ok, f"profileUpdate 失败 status={resp.status}"
        step_shot_after_success_toast(page_obj, "step_after_save_success")

    # 不在 Allure 展示“回到 baseline”过程；仍回填 UI，确保本用例内部不留脏状态（落库回滚由 fixture teardown 决策）
    settle_toasts(page_obj)
    page_obj.fill_form(initial)
    current = page_obj.read_form_values()
    for k in ("userName", "name", "surname", "email", "phoneNumber"):
        assert (current.get(k) or "") == (initial.get(k) or "")

    logger.end(success=True)


#
# NOTE:
# - test_p0_profile_settings_email_required / test_p0_profile_settings_username_required
#   已在 P1 matrix 中覆盖（且覆盖更系统），为避免重复与执行耗时，这里删除 P0 重复用例。
