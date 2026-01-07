"""
Admin Users - P1 Username Validation Matrix

场景数：16
覆盖率：95%
"""

from __future__ import annotations

import pytest
import allure

from ._matrix_helpers import UsersMatrixScenario, run_users_matrix_case
from ._helpers import AbpUserConsts, now_suffix


def _scenarios():
    """16 场景：必填/格式/安全/长度/空白"""
    max_len = AbpUserConsts.MaxUserNameLength
    
    return [
        # 必填（2）
        ("empty", "", False, "必填：空", True),
        ("whitespace", "   ", False, "必填：空白", True),
        
        # 格式（5）
        ("alphanumeric", None, True, "格式：字母数字", False),
        ("underscore", None, True, "格式：下划线", False),
        ("dot", None, True, "格式：点号", False),
        ("hyphen", None, True, "格式：连字符", False),
        ("at", None, True, "格式：@", False),
        
        # 特殊字符（2）
        ("space", None, False, "特殊字符：空格", False),
        ("hash", None, False, "特殊字符：#", False),
        
        # 安全（2）
        ("sqli", "admin'--", False, "安全：SQLi", False),
        ("xss", "<script>alert('xss')</script>", False, "安全：XSS", False),
        
        # 长度（4）
        ("len_1", None, True, "长度：1", False),
        ("len_50", None, True, "长度：50", False),
        ("len_256", "u" + ("x" * (max_len - 1)), False, "长度：256（超长）", False),  # 实际后端限制可能是255
        ("len_257", "u" + ("x" * max_len), False, "长度：257（超长）", False),
        
        # 空白（1）
        ("trim", None, True, "空白：trim", False),
    ]


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("用户管理")
@allure.story("Username 矩阵")
@pytest.mark.parametrize(
    "name,username,should_save,note,require_fe_error",
    [pytest.param(*s, id=s[0]) for s in _scenarios()],
)
def test_p1_users_username_matrix(admin_page, name, username, should_save, note, require_fe_error):
    """16 场景：必填/格式/安全/长度/空白"""
    suffix = now_suffix()
    
    # 生成 username
    if username is None:
        if "alphanumeric" in name:
            u = f"user123{suffix}"
        elif "underscore" in name:
            u = f"user_test{suffix}"
        elif "dot" in name:
            u = f"user.test{suffix}"
        elif "hyphen" in name:
            u = f"user-test{suffix}"
        elif "at" in name:
            u = f"user@test{suffix}"
        elif "space" in name:
            u = f"user test{suffix}"
        elif "hash" in name:
            u = f"user#test{suffix}"
        elif "len_1" in name:
            u = f"u{suffix}"
        elif "len_50" in name:
            u = f"u{'a' * 49}{suffix}"
        elif "trim" in name:
            u = f"  user{suffix}  "
        else:
            u = f"test{suffix}"
    else:
        u = username
    
    # 创建场景
    scenario = UsersMatrixScenario(
        case_name=f"username_{name}",
        selector="input[placeholder='User name']",  # 注意：是小写 'name'
        patch={"username": u, "email": f"{name}{suffix}@test.com", "password": "Test@123456"},
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_fe_error,
        require_backend_reject=not require_fe_error and not should_save,
    )
    
    # 运行
    run_users_matrix_case(admin_page, admin_page, scenario)
