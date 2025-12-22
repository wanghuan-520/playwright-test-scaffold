"""
Profile Settings - P1 PhoneNumber Validation Matrix
"""

from __future__ import annotations

import allure  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]

from utils.logger import TestLogger
from ._helpers import AbpUserConsts
from ._matrix_helpers import MatrixScenario, rand_suffix, run_matrix_case


@pytest.mark.P1
@pytest.mark.validation
@pytest.mark.matrix
@allure.feature("Profile Settings")
@allure.story("P1 - PhoneNumber Validation Matrix")
@allure.description(
    """
测试点（phoneNumber，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 形态：数字、字母、中文（按 ABP 默认不限制字符集）
- 例外：'+86 138 0013 8000' 在当前前端会被拦截（不发请求），按“无效应失败/应阻止”记为不应保存
- 长度：最大 16 / 超长 17
- 证据：每个场景 2 张关键截图（filled / result）
"""
)
def test_p1_profile_phone_validation_matrix(profile_settings):
    logger = TestLogger("test_p1_profile_phone_validation_matrix")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    suf = rand_suffix(auth_page)

    max_len = AbpUserConsts.MaxPhoneNumberLength
    phone_max = "1" * max_len
    phone_over = "2" * (max_len + 1)

    scenarios = [
        MatrixScenario("phone_empty", page_obj.PHONE_INPUT, {"phoneNumber": ""}, True, "可空"),
        MatrixScenario("phone_whitespace", page_obj.PHONE_INPUT, {"phoneNumber": "   "}, True, "可空/空白"),
        MatrixScenario("phone_digits", page_obj.PHONE_INPUT, {"phoneNumber": f"138{suf}"[:11]}, True, "数字"),
        # 该环境下 phoneNumber 输入会被前端拦截（不发请求）——按“无效应失败/应阻止”的原则当作不应保存
        MatrixScenario(
            "phone_plus_space",
            page_obj.PHONE_INPUT,
            {"phoneNumber": "+86 138 0013 8000"},
            False,
            "+/空格（前端应拦截）",
            require_frontend_error_evidence=True,
        ),
        MatrixScenario("phone_alpha", page_obj.PHONE_INPUT, {"phoneNumber": f"abc{suf}"[:10]}, True, "字母（ABP 默认允许）"),
        MatrixScenario("phone_cn", page_obj.PHONE_INPUT, {"phoneNumber": f"电话{suf}"[:10]}, True, "中文（ABP 默认允许）"),
        MatrixScenario("phone_len_max_16", page_obj.PHONE_INPUT, {"phoneNumber": phone_max}, True, "最大长度 16"),
        MatrixScenario("phone_len_over_17", page_obj.PHONE_INPUT, {"phoneNumber": phone_over}, False, "超长 17", require_frontend_error_evidence=True),
    ]

    for sc in scenarios:
        run_matrix_case(auth_page, page_obj, baseline, sc)

    logger.end(success=True)

