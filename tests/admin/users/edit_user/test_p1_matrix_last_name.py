"""
Admin Users - Edit User P1 Last Name Validation Matrix

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
def _last_name_scenarios():
    """
    生成参数化场景：9个场景，包含完整边界值测试
    """
    max_len = AbpUserConsts.MaxSurnameLength  # 64
    surname_max_minus_1 = "S" * (max_len - 1)  # 63
    surname_max = "S" * max_len  # 64
    surname_max_plus_1 = "S" * (max_len + 1)  # 65
    
    scenarios = [
        ("last_name_empty", {"lastName": ""}, True, "可空", False, False, False),
        ("last_name_whitespace", {"lastName": "   "}, True, "可空/空白", False, False, False),
        ("last_name_en", {"lastName": "Smith-"}, True, "英文/连字符", True, False, False),
        ("last_name_cn", {"lastName": "李"}, True, "中文允许（ABP 默认）", True, False, False),
        ("last_name_mix_special", {"lastName": "Von_O'Brien."}, True, "特殊字符允许（ABP 默认）", True, False, False),
        ("last_name_emoji", {"lastName": "Test🙂"}, True, "Emoji", True, False, False),
        ("last_name_len_max_minus_1", {"lastName": surname_max_minus_1}, True, "最大长度-1（63）应成功", False, False, False),
        ("last_name_len_max_64", {"lastName": surname_max}, True, "最大长度（64）应成功", False, False, False),
        ("last_name_len_max_plus_1", {"lastName": surname_max_plus_1}, True, "超长（65）前端 maxLength=64 截断为 64 → 保存成功", False, False, False),
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
@allure.story("P1 - Edit User - Last Name Validation Matrix")
@allure.description(
    """
测试点（Last Name，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 字符集：英文/连字符、中文、常见特殊字符、Emoji（按 ABP 默认）
- 长度：最大 64 / 超长 65（MongoDB 可能接受）
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject",
    _last_name_scenarios(),
)
def test_p1_edit_user_last_name_validation_matrix(
    auth_page,
    case_name: str,
    patch: dict,
    should_save: bool,
    note: str,
    need_suffix: bool,
    require_frontend_error: bool,
    require_backend_reject: bool,
):
    logger = TestLogger(f"test_p1_edit_user_last_name_validation_matrix[{case_name}]")
    logger.start()
    
    page_obj = AdminUsersPage(auth_page)
    # 创建专门用于编辑的测试用户，避免污染账号池
    test_user = generate_unique_user("edit_lastname_test")
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
                    patch_copy[k] = f"{v}_{suf}"
                else:
                    patch_copy[k] = v
            patch = patch_copy
        
        # 构造 MatrixScenario 并执行
        scenario = EditUserMatrixScenario(
            case_name=case_name,
            selector="EDIT_USER_LAST_NAME_INPUT",  # 仅用于错误检查
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

