"""
Profile Settings - P1 PhoneNumber Validation Matrix

优化说明：
- 将原 for 循环改为 pytest.mark.parametrize，每个场景独立执行
- 可充分利用 pytest-xdist 并行能力，显著提升速度
"""

from __future__ import annotations

import allure  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]

from utils.logger import TestLogger
from tests.admin.profile._helpers import AbpUserConsts
from tests.admin.profile._matrix_helpers import MatrixScenario, rand_suffix, run_matrix_case


# ═══════════════════════════════════════════════════════════════
# 参数化场景列表
# ═══════════════════════════════════════════════════════════════
def _phone_scenarios():
    """
    生成参数化场景：8个场景，包含完整边界值测试
    """
    max_len = AbpUserConsts.MaxPhoneNumberLength  # 16
    phone_max_minus_1 = "1" * (max_len - 1)  # 15
    phone_max = "1" * max_len  # 16
    phone_max_plus_1 = "2" * (max_len + 1)  # 17
    
    scenarios = [
        ("phone_empty", "PHONE_INPUT", {"phoneNumber": ""}, True, "可空", False, False, False),
        ("phone_whitespace", "PHONE_INPUT", {"phoneNumber": "   "}, True, "可空/空白", False, False, False),
        ("phone_digits", "PHONE_INPUT", {"phoneNumber": "138"}, True, "数字", True, False, False),
        ("phone_alpha", "PHONE_INPUT", {"phoneNumber": "abc"}, True, "字母（ABP 默认允许）", True, False, False),
        ("phone_cn", "PHONE_INPUT", {"phoneNumber": "电话"}, True, "中文（ABP 默认允许）", True, False, False),
        ("phone_len_max_minus_1", "PHONE_INPUT", {"phoneNumber": phone_max_minus_1}, True, "最大长度-1（15）应成功", False, False, False),
        ("phone_len_max_16", "PHONE_INPUT", {"phoneNumber": phone_max}, True, "最大长度（16）应成功", False, False, False),
        ("phone_len_max_plus_1", "PHONE_INPUT", {"phoneNumber": phone_max_plus_1}, False, "超长（17）应失败", False, False, False),
    ]
    
    params = []
    for case_name, selector_attr, patch, should_save, note, need_suffix, require_frontend_error, require_backend_reject in scenarios:
        params.append(
            pytest.param(
                case_name,
                selector_attr,
                patch,
                should_save,
                note,
                need_suffix,
                require_frontend_error,
                require_backend_reject,
                id=case_name,
            )
        )
    return params


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("Profile Settings")
@allure.story("P1 - PhoneNumber Validation Matrix")
@allure.description(
    """
测试点（phoneNumber，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 形态：数字、字母、中文（按 ABP 默认不限制字符集）
- 例外：'+86 138 0013 8000' 在当前前端会被拦截（不发请求），按"无效应失败/应阻止"记为不应保存
- 长度：最大 16 / 超长 17
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,selector_attr,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject",
    _phone_scenarios(),
)
def test_p1_profile_phone_validation_matrix(
    profile_settings,
    case_name: str,
    selector_attr: str,
    patch: dict,
    should_save: bool,
    note: str,
    need_suffix: bool,
    require_frontend_error: bool,
    require_backend_reject: bool,
):
    logger = TestLogger(f"test_p1_profile_phone_validation_matrix[{case_name}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    
    # 动态添加 suffix（如果需要）
    if need_suffix:
        suf = rand_suffix(auth_page)
        patch_copy = {}
        for k, v in patch.items():
            if isinstance(v, str) and v:
                # phone: 截取到最大长度
                combined = f"{v}{suf}"[:AbpUserConsts.MaxPhoneNumberLength]
                patch_copy[k] = combined[:11]  # 限制手机号长度
            else:
                patch_copy[k] = v
        patch = patch_copy
    
    # 获取 selector
    selector = getattr(page_obj, selector_attr)
    
    # 构造 MatrixScenario 并执行
    scenario = MatrixScenario(
        case_name=case_name,
        selector=selector,
        patch=patch,
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_frontend_error,
        require_backend_reject=require_backend_reject,
        allow_taken_conflict=False,
    )
    
    run_matrix_case(auth_page, page_obj, baseline, scenario)

    logger.end(success=True)
