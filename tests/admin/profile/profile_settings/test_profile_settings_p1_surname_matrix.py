"""
Profile Settings - P1 Surname Validation Matrix

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
def _surname_scenarios():
    """
    生成参数化场景：9个场景，包含完整边界值测试
    """
    max_len = AbpUserConsts.MaxSurnameLength  # 64
    surname_max_minus_1 = "S" * (max_len - 1)  # 63
    surname_max = "S" * max_len  # 64
    surname_max_plus_1 = "S" * (max_len + 1)  # 65
    
    scenarios = [
        ("surname_empty", "SURNAME_INPUT", {"surname": ""}, True, "可空", False, False, False),
        ("surname_whitespace", "SURNAME_INPUT", {"surname": "   "}, True, "可空/空白", False, False, False),
        ("surname_en", "SURNAME_INPUT", {"surname": "Smith-"}, True, "英文/连字符", True, False, False),
        ("surname_cn", "SURNAME_INPUT", {"surname": "李"}, True, "中文允许（ABP 默认）", True, False, False),
        ("surname_mix_special", "SURNAME_INPUT", {"surname": "Von_O'Brien."}, True, "特殊字符允许（ABP 默认）", True, False, False),
        ("surname_emoji", "SURNAME_INPUT", {"surname": "Test🙂"}, True, "Emoji", True, False, False),
        ("surname_len_max_minus_1", "SURNAME_INPUT", {"surname": surname_max_minus_1}, True, "最大长度-1（63）应成功", False, False, False),
        ("surname_len_max_64", "SURNAME_INPUT", {"surname": surname_max}, True, "最大长度（64）应成功", False, False, False),
        ("surname_len_max_plus_1", "SURNAME_INPUT", {"surname": surname_max_plus_1}, False, "超长（65）应失败", False, False, False),
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
@allure.story("P1 - Surname Validation Matrix")
@allure.description(
    """
测试点（surname，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 字符集：英文/连字符、中文、常见特殊字符、Emoji（按 ABP 默认）
- 长度：最大 64 / 超长 65
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,selector_attr,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject",
    _surname_scenarios(),
)
def test_p1_profile_surname_validation_matrix(
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
    logger = TestLogger(f"test_p1_profile_surname_validation_matrix[{case_name}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    
    # 动态添加 suffix（如果需要）
    if need_suffix:
        suf = rand_suffix(auth_page)
        patch_copy = {}
        for k, v in patch.items():
            if isinstance(v, str) and v:
                patch_copy[k] = f"{v}_{suf}"
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
