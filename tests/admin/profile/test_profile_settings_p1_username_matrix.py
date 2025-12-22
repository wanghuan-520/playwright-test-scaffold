"""
Profile Settings - P1 Username Validation Matrix
"""

from __future__ import annotations

import re

import allure  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]

from utils.logger import TestLogger
from ._helpers import AbpUserConsts
from ._matrix_helpers import MatrixScenario, rand_suffix, run_matrix_case


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
"""
)
def test_p1_profile_username_validation_matrix(profile_settings):
    logger = TestLogger("test_p1_profile_username_validation_matrix")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    suf = rand_suffix(auth_page)

    assert re.match(AbpUserConsts.UserNamePattern, "user_1"), "sanity: AbpUserConsts.UserNamePattern invalid"

    scenarios = [
        MatrixScenario("username_required_empty", page_obj.USERNAME_INPUT, {"userName": ""}, False, "必填", require_frontend_error_evidence=True),
        MatrixScenario("username_required_whitespace", page_obj.USERNAME_INPUT, {"userName": "   "}, False, "必填/正则不允许空白", require_frontend_error_evidence=True),
        MatrixScenario("username_ok_plain", page_obj.USERNAME_INPUT, {"userName": f"TestUser{suf}"}, True, "纯英文数字"),
        MatrixScenario("username_ok_underscore", page_obj.USERNAME_INPUT, {"userName": f"user_123_{suf}"}, True, "下划线允许"),
        MatrixScenario("username_ok_dot_dash", page_obj.USERNAME_INPUT, {"userName": f"test.user-name.{suf}"}, True, "点/连字符允许"),
        MatrixScenario("username_ok_at", page_obj.USERNAME_INPUT, {"userName": f"user@{suf}.com"}, True, "@ 允许（ABP 默认）"),
        MatrixScenario("username_ok_numeric", page_obj.USERNAME_INPUT, {"userName": f"123{suf}"}, True, "纯数字允许"),
        MatrixScenario("username_bad_space", page_obj.USERNAME_INPUT, {"userName": f"user {suf} name"}, False, "包含空格", require_frontend_error_evidence=True),
        MatrixScenario("username_bad_special_1", page_obj.USERNAME_INPUT, {"userName": f"user{suf}!@#$%"}, False, "包含 !#$%", require_frontend_error_evidence=True),
        MatrixScenario("username_bad_special_2", page_obj.USERNAME_INPUT, {"userName": f"user{suf}*&^"}, False, "包含 *&^", require_frontend_error_evidence=True),
        MatrixScenario("username_bad_cn", page_obj.USERNAME_INPUT, {"userName": f"测试用户{suf}"}, False, "包含中文", require_frontend_error_evidence=True),
        MatrixScenario(
            "username_len_min_1",
            page_obj.USERNAME_INPUT,
            {"userName": f"u{suf}"[:1]},
            True,
            "最小长度 1（共享环境可能撞到已存在用户名：允许 already taken 作为可接受结果）",
            allow_taken_conflict=True,
        ),
        MatrixScenario("username_len_normal_50", page_obj.USERNAME_INPUT, {"userName": (f"u{suf}" + ("a" * 60))[:50]}, True, "正常长度 50"),
        MatrixScenario("username_len_max_256", page_obj.USERNAME_INPUT, {"userName": (f"u{suf}" + ("x" * 300))[: AbpUserConsts.MaxUserNameLength]}, True, "最大长度 256"),
        MatrixScenario(
            "username_len_over_257",
            page_obj.USERNAME_INPUT,
            {"userName": (f"u{suf}" + ("y" * 400))[: AbpUserConsts.MaxUserNameLength + 1]},
            False,
            "超长 257",
            require_frontend_error_evidence=True,
        ),
    ]

    for sc in scenarios:
        run_matrix_case(auth_page, page_obj, baseline, sc)

    logger.end(success=True)

