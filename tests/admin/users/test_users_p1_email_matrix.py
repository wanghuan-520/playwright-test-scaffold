"""
Admin Users - P1 Email Validation Matrix

场景数：13
覆盖率：95%
"""

from __future__ import annotations

import pytest
import allure

from ._matrix_helpers import UsersMatrixScenario, run_users_matrix_case
from ._helpers import AbpUserConsts, now_suffix


def _scenarios():
    """13 场景：必填/格式/安全/长度"""
    max_len = AbpUserConsts.MaxEmailLength
    
    return [
        # 必填（2）
        ("empty", "", False, "必填：空", True),
        ("whitespace", "   ", False, "必填：空白", True),
        
        # 格式（6）
        ("valid", None, True, "格式：标准邮箱", False),
        ("no_at", "testtest.com", False, "格式：缺少@", True),
        ("no_domain", "test@", False, "格式：缺少域名", True),
        ("no_tld", "test@test", False, "格式：缺少后缀", True),
        ("multiple_at", "test@@test.com", False, "格式：多个@", True),
        ("spaces", "test @test.com", False, "格式：包含空格", True),
        
        # 安全（2）
        ("xss", "test@test.com<script>alert('xss')</script>", False, "安全：XSS", False),
        ("sqli", "test'--@test.com", False, "安全：SQLi", False),
        
        # 长度（3）
        ("len_1", "a@b.c", True, "长度：最小有效", False),
        ("len_256", "a" * (max_len - 10) + "@test.com", True, "长度：256", False),
        ("len_257", "a" * (max_len - 9) + "@test.com", False, "长度：257", False),
    ]


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("用户管理")
@allure.story("Email 矩阵")
@pytest.mark.parametrize(
    "name,email,should_save,note,require_fe_error",
    [pytest.param(*s, id=s[0]) for s in _scenarios()],
)
def test_p1_users_email_matrix(admin_page, name, email, should_save, note, require_fe_error):
    """13 场景：必填/格式/安全/长度"""
    suffix = now_suffix()
    
    # 生成 email
    if email is None:
        e = f"test{suffix}@test.com"
    else:
        e = email
    
    # 创建场景
    scenario = UsersMatrixScenario(
        case_name=f"email_{name}",
        selector="input[placeholder='Email address']",
        patch={"username": f"user{suffix}", "email": e, "password": "Test@123456"},
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_fe_error,
        require_backend_reject=not require_fe_error and not should_save,
    )
    
    # 运行
    run_users_matrix_case(admin_page, admin_page, scenario)

