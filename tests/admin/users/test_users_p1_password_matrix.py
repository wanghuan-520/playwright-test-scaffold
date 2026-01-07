"""
Admin Users - P1 Password Validation Matrix

场景数：15
覆盖率：95%
"""

from __future__ import annotations

import pytest
import allure

from ._matrix_helpers import UsersMatrixScenario, run_users_matrix_case
from ._helpers import AbpUserConsts, now_suffix


def _scenarios():
    """15 场景：必填/强度/长度"""
    min_len = AbpUserConsts.MinPasswordLength
    max_len = AbpUserConsts.MaxPasswordLength
    
    return [
        # 必填（2）
        ("empty", "", False, "必填：空", True),
        ("whitespace", "   ", False, "必填：空白", True),
        
        # 强度（7）
        ("weak_123456", "123456", False, "强度：纯数字", False),
        ("weak_abc", "abcdefg", False, "强度：纯小写", False),
        ("weak_ABC", "ABCDEFG", False, "强度：纯大写", False),
        ("medium_Abc123", "Abcdef123", False, "强度：缺少特殊字符", False),
        ("strong", "Test@123456", True, "强度：强密码", False),
        ("strong_complex", "P@ssw0rd!2023", True, "强度：复杂密码", False),
        ("strong_special", "Test#$%^&*()123", True, "强度：多种特殊字符", False),
        
        # 长度（4）
        ("len_5", "Ab@12", False, "长度：5（太短）", False),
        ("len_6", "Ab@123", True, "长度：6（最小）", False),
        ("len_20", "Ab@" + ("1" * 17), True, "长度：20", False),
        ("len_128", "Ab@" + ("1" * (max_len - 4)), True, "长度：128（最大）", False),
        ("len_129", "Ab@" + ("1" * (max_len - 3)), False, "长度：129（超长）", False),
        
        # 安全（2）
        ("sqli", "' OR '1'='1", False, "安全：SQLi", False),
        ("xss", "<script>alert('xss')</script>", False, "安全：XSS", False),
    ]


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("用户管理")
@allure.story("Password 矩阵")
@pytest.mark.parametrize(
    "name,password,should_save,note,require_fe_error",
    [pytest.param(*s, id=s[0]) for s in _scenarios()],
)
def test_p1_users_password_matrix(admin_page, name, password, should_save, note, require_fe_error):
    """15 场景：必填/强度/长度"""
    suffix = now_suffix()
    
    # 创建场景
    scenario = UsersMatrixScenario(
        case_name=f"password_{name}",
        selector="input[placeholder='Password']",
        patch={"username": f"user{suffix}", "email": f"test{suffix}@test.com", "password": password},
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_fe_error,
        require_backend_reject=not require_fe_error and not should_save,
    )
    
    # 运行
    run_users_matrix_case(admin_page, admin_page, scenario)

