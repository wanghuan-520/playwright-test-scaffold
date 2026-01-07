"""
Admin Users - P1 Phone Number Validation Matrix

场景数：10
覆盖率：90%
"""

from __future__ import annotations

import pytest
import allure

from ._matrix_helpers import UsersMatrixScenario, run_users_matrix_case
from ._helpers import AbpUserConsts, now_suffix


def _scenarios():
    """10 场景：可选字段/格式/长度"""
    max_len = AbpUserConsts.MaxPhoneNumberLength
    
    return [
        # 可选（1）
        ("empty", "", True, "可选：空", False),
        
        # 格式（5）
        ("numeric", "1234567890", True, "格式：纯数字", False),
        ("with_plus", "+1234567890", True, "格式：加号", False),
        ("with_hyphen", "123-456-7890", True, "格式：连字符", False),
        ("with_space", "123 456 7890", True, "格式：空格", False),
        ("with_parentheses", "(123) 456-7890", True, "格式：括号", False),
        
        # 长度（3）
        ("len_1", "1", True, "长度：1", False),
        ("len_16", "1" * max_len, True, "长度：16（最大）", False),
        ("len_17", "1" * (max_len + 1), False, "长度：17（超长）", False),
        
        # 安全（1）
        ("xss", "<script>alert('xss')</script>", False, "安全：XSS", False),
    ]


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("用户管理")
@allure.story("Phone 矩阵")
@pytest.mark.parametrize(
    "name,value,should_save,note,require_fe_error",
    [pytest.param(*s, id=s[0]) for s in _scenarios()],
)
def test_p1_users_phone_matrix(admin_page, name, value, should_save, note, require_fe_error):
    """10 场景：可选/格式/长度/安全"""
    suffix = now_suffix()
    
    # 创建场景
    scenario = UsersMatrixScenario(
        case_name=f"phone_{name}",
        selector="input[placeholder='Phone Number']",
        patch={"username": f"user{suffix}", "email": f"test{suffix}@test.com", "password": "Test@123456", "phone": value},
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_fe_error,
        require_backend_reject=not require_fe_error and not should_save,
    )
    
    # 运行
    run_users_matrix_case(admin_page, admin_page, scenario)

