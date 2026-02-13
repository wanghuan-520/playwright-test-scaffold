"""
Admin Users - Edit User P1 Phone Number Validation Matrix

优化说明：
- 使用 pytest.mark.parametrize，每个场景独立执行
- 可充分利用 pytest-xdist 并行能力，显著提升速度
"""

from __future__ import annotations

import allure
import pytest

from utils.logger import TestLogger
from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import (
    AbpUserConsts,
    generate_unique_user,
    create_test_user,
    delete_test_user,
)
from tests.admin.users.edit_user._matrix_helpers import (
    EditUserMatrixScenario,
    run_edit_user_matrix_case,
)
from tests.myaccount._matrix_helpers import rand_suffix


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
        ("phone_empty", {"phone": ""}, True, "可空", False, False, False),
        ("phone_whitespace", {"phone": "   "}, True, "可空/空白", False, False, False),
        ("phone_digits", {"phone": "138"}, True, "数字", True, False, False),
        ("phone_alpha", {"phone": "abc"}, True, "字母（ABP 默认允许）", True, False, False),
        ("phone_cn", {"phone": "电话"}, True, "中文（ABP 默认允许）", True, False, False),
        ("phone_len_max_minus_1", {"phone": phone_max_minus_1}, True, "最大长度-1（15）应成功", False, False, False),
        ("phone_len_max_16", {"phone": phone_max}, True, "最大长度（16）应成功", False, False, False),
        ("phone_len_max_plus_1", {"phone": phone_max_plus_1}, False, "超长（17）应失败（MongoDB 可能接受）", False, False, False),
    ]
    
    params = []
    for case_name, patch, should_save, note, need_suffix, require_frontend_error, require_backend_reject in scenarios:
        params.append(
            pytest.param(
                case_name,
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
@pytest.mark.admin
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("Admin Users")
@allure.story("P1 - Edit User - Phone Number Validation Matrix")
@allure.description(
    """
测试点（Phone Number，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 形态：数字、字母、中文（按 ABP 默认不限制字符集）
- 长度：最大 16 / 超长 17（MongoDB 可能接受）
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject",
    _phone_scenarios(),
)
def test_p1_edit_user_phone_validation_matrix(
    auth_page,
    case_name: str,
    patch: dict,
    should_save: bool,
    note: str,
    need_suffix: bool,
    require_frontend_error: bool,
    require_backend_reject: bool,
):
    logger = TestLogger(f"test_p1_edit_user_phone_validation_matrix[{case_name}]")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_phone_test")
    created_users = []
    
    try:
        with allure.step("创建专门用于编辑的测试用户"):
            create_test_user(page_obj, test_user)
            created_users.append(test_user["username"])
            page_obj.wait_for_data_loaded(timeout=3000)  # 优化：进一步减少超时
            allure.attach(f"创建的测试用户: {test_user['username']}", "test_user_info")
        
        # 动态添加 suffix（如果需要）
        if need_suffix:
            suf = rand_suffix(auth_page)
            patch_copy = {}
            for k, v in patch.items():
                if isinstance(v, str) and v:
                    if k == "phone":
                        # phone: 截取到最大长度
                        combined = f"{v}{suf}"[:AbpUserConsts.MaxPhoneNumberLength]
                        patch_copy[k] = combined[:11]  # 限制手机号长度
                    else:
                        patch_copy[k] = f"{v}_{suf}"
                else:
                    patch_copy[k] = v
            patch = patch_copy
        
        # 构造 MatrixScenario 并执行
        scenario = EditUserMatrixScenario(
            case_name=case_name,
            selector="EDIT_USER_PHONE_INPUT",  # 仅用于错误检查
            patch=patch,
            should_save=should_save,
            note=note,
            require_frontend_error_evidence=require_frontend_error,
            require_backend_reject=require_backend_reject,
            allow_taken_conflict=False,
        )
        
        run_edit_user_matrix_case(auth_page, page_obj, test_user["username"], scenario)
        
        logger.end(success=True)
        
    finally:
        # 清理测试用户
        for username in created_users:
            try:
                delete_test_user(page_obj, username)
            except Exception:
                pass

