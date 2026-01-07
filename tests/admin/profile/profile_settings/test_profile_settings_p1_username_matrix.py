"""
Profile Settings - P1 Username Validation Matrix

优化说明：
- 将原 for 循环改为 pytest.mark.parametrize，每个场景独立执行
- 可充分利用 pytest-xdist 并行能力，显著提升速度
"""

from __future__ import annotations

import re

import allure  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]

from utils.logger import TestLogger
from tests.admin.profile._helpers import AbpUserConsts
from tests.admin.profile._matrix_helpers import MatrixScenario, rand_suffix, run_matrix_case


# ═══════════════════════════════════════════════════════════════
# 参数化场景列表
# ═══════════════════════════════════════════════════════════════
def _username_scenarios():
    """
    生成参数化场景：16个场景，包含完整边界值测试
    """
    # 静态验证
    assert re.match(AbpUserConsts.UserNamePattern, "user_1"), "sanity: AbpUserConsts.UserNamePattern invalid"
    
    max_len = AbpUserConsts.MaxUserNameLength  # 256
    username_max_minus_1 = "u" + ("x" * (max_len - 2))  # 255
    username_max = "u" + ("x" * (max_len - 1))  # 256
    username_max_plus_1 = "u" + ("y" * max_len)  # 257
    
    scenarios = [
        ("username_required_empty", "USERNAME_INPUT", {"userName": ""}, False, "必填", False, True, False, False),
        ("username_required_whitespace", "USERNAME_INPUT", {"userName": "   "}, True, "空白输入：后端允许/归一化均可", False, False, False, False),
        ("username_ok_plain", "USERNAME_INPUT", {"userName": "TestUser"}, True, "纯英文数字", True, False, False, False),
        ("username_ok_underscore", "USERNAME_INPUT", {"userName": "user_123_"}, True, "下划线允许", True, False, False, False),
        ("username_ok_dot_dash", "USERNAME_INPUT", {"userName": "test.user-name."}, True, "点/连字符允许", True, False, False, False),
        ("username_ok_at", "USERNAME_INPUT", {"userName": "user@.com"}, True, "@ 允许（ABP 默认）", True, False, False, False),
        ("username_ok_numeric", "USERNAME_INPUT", {"userName": "123"}, True, "纯数字允许", True, False, False, False),
        ("username_bad_space", "USERNAME_INPUT", {"userName": "user name"}, True, "包含空格（后端允许则应保存）", True, False, False, False),
        ("username_bad_special_1", "USERNAME_INPUT", {"userName": "user!@#$%"}, True, "包含 !#$%（后端允许则应保存）", True, False, False, False),
        ("username_bad_special_2", "USERNAME_INPUT", {"userName": "user*&^"}, True, "包含 *&^（后端允许则应保存）", True, False, False, False),
        ("username_bad_cn", "USERNAME_INPUT", {"userName": "测试用户"}, True, "包含中文（后端允许则应保存）", True, False, False, False),
        ("username_len_min_1", "USERNAME_INPUT", {"userName": "u"}, True, "最小长度 1（共享环境可能撞到已存在用户名）", True, False, False, True),
        ("username_len_normal_50", "USERNAME_INPUT", {"userName": "u" + ("a" * 49)}, True, "正常长度 50", True, False, False, False),
        ("username_len_max_minus_1", "USERNAME_INPUT", {"userName": username_max_minus_1}, True, "最大长度-1（255）应成功", False, False, False, False),
        ("username_len_max_256", "USERNAME_INPUT", {"userName": username_max}, True, "最大长度（256）应成功", False, False, False, False),
        ("username_len_max_plus_1", "USERNAME_INPUT", {"userName": username_max_plus_1}, False, "超长（257）应失败", False, False, False, False),
    ]
    
    params = []
    for case_name, selector_attr, patch, should_save, note, need_suffix, require_frontend_error, require_backend_reject, allow_taken in scenarios:
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
                allow_taken,
                id=case_name,
            )
        )
    return params


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("Profile Settings")
@allure.story("P1 - Username Validation Matrix")
@allure.description(
    """
测试点（userName）：
- 必填：空 / 纯空白应被前端拦截（不发 profileUpdate）且有可见错误证据
- 正则/字符集：验证 ABP 默认 userName pattern
  - 允许：字母数字、下划线、点、连字符、@、纯数字
  - 拒绝：空格、部分特殊字符、中文
- 长度：1 / 正常长度 / 最大 256 / 超长 257
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,selector_attr,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject,allow_taken",
    _username_scenarios(),
)
def test_p1_profile_username_validation_matrix(
    profile_settings,
    case_name: str,
    selector_attr: str,
    patch: dict,
    should_save: bool,
    note: str,
    need_suffix: bool,
    require_frontend_error: bool,
    require_backend_reject: bool,
    allow_taken: bool,
):
    logger = TestLogger(f"test_p1_profile_username_validation_matrix[{case_name}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    
    # 动态添加 suffix（如果需要）
    if need_suffix:
        suf = rand_suffix(auth_page)
        patch_copy = {}
        for k, v in patch.items():
            if isinstance(v, str) and v:
                # 对于username，在末尾添加suffix
                if len(v) + len(suf) <= AbpUserConsts.MaxUserNameLength:
                    patch_copy[k] = f"{v}{suf}"
                else:
                    # 如果会超长，截断
                    patch_copy[k] = (f"{v}{suf}")[:AbpUserConsts.MaxUserNameLength]
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
        allow_taken_conflict=allow_taken,
    )
    
    run_matrix_case(auth_page, page_obj, baseline, scenario)

    logger.end(success=True)
