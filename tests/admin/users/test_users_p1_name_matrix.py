"""
Admin Users - P1 Name Validation Matrix

场景数：10
覆盖率：90%
"""

from __future__ import annotations

import pytest
import allure

from ._matrix_helpers import UsersMatrixScenario, run_users_matrix_case
from ._helpers import AbpUserConsts, now_suffix


def _scenarios():
    """10 场景：可选字段/长度/特殊字符"""
    max_len = AbpUserConsts.MaxNameLength
    
    return [
        # 可选（1）
        ("empty", "", True, "可选：空", False),
        
        # 格式（5）
        ("alphanumeric", None, True, "格式：字母", False),
        ("with_space", None, True, "格式：包含空格", False),
        ("chinese", "测试", True, "格式：中文", False),
        ("special", "Name's", True, "格式：特殊字符", False),
        ("numbers", "Name123", True, "格式：数字", False),
        
        # 长度（3）
        ("len_1", "A", True, "长度：1", False),
        ("len_64", "A" * max_len, True, "长度：64（最大）", False),
        ("len_65", "A" * (max_len + 1), False, "长度：65（超长）", False),
        
        # 安全（1）
        ("xss", "<script>alert('xss')</script>", False, "安全：XSS", False),
    ]


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("用户管理")
@allure.story("Name 矩阵")
@pytest.mark.parametrize(
    "name,value,should_save,note,require_fe_error",
    [pytest.param(*s, id=s[0]) for s in _scenarios()],
)
def test_p1_users_name_matrix(admin_page, name, value, should_save, note, require_fe_error):
    """10 场景：可选/格式/长度/安全"""
    suffix = now_suffix()
    
    # 生成 name 值
    if value is None:
        if "alphanumeric" in name:
            n = "John"
        elif "space" in name:
            n = "John Doe"
        else:
            n = f"Name{suffix}"
    else:
        n = value
    
    # 创建场景
    scenario = UsersMatrixScenario(
        case_name=f"name_{name}",
        selector="input[placeholder='Name']",
        patch={"username": f"user{suffix}", "email": f"test{suffix}@test.com", "password": "Test@123456", "name": n},
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_fe_error,
        require_backend_reject=not require_fe_error and not should_save,
    )
    
    # 运行
    run_users_matrix_case(admin_page, admin_page, scenario)

