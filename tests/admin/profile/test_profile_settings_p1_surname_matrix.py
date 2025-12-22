"""
Profile Settings - P1 Surname Validation Matrix
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
@allure.story("P1 - Surname Validation Matrix")
@allure.description(
    """
测试点（surname，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 字符集：英文/连字符、中文、常见特殊字符、Emoji（按 ABP 默认）
- 长度：最大 64 / 超长 65
- 证据：每个场景 2 张关键截图（filled / result）
"""
)
def test_p1_profile_surname_validation_matrix(profile_settings):
    logger = TestLogger("test_p1_profile_surname_validation_matrix")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    suf = rand_suffix(auth_page)

    max_len = AbpUserConsts.MaxSurnameLength
    surname_max = "S" * max_len
    surname_over = "T" * (max_len + 1)

    scenarios = [
        MatrixScenario("surname_empty", page_obj.SURNAME_INPUT, {"surname": ""}, True, "可空"),
        MatrixScenario("surname_whitespace", page_obj.SURNAME_INPUT, {"surname": "   "}, True, "可空/空白"),
        MatrixScenario("surname_en", page_obj.SURNAME_INPUT, {"surname": f"Smith-{suf}"}, True, "英文/连字符"),
        MatrixScenario("surname_cn", page_obj.SURNAME_INPUT, {"surname": f"李{suf}"}, True, "中文允许（ABP 默认）"),
        MatrixScenario("surname_mix_special", page_obj.SURNAME_INPUT, {"surname": f"Von_O'Brien.{suf}"}, True, "特殊字符允许（ABP 默认）"),
        MatrixScenario("surname_emoji", page_obj.SURNAME_INPUT, {"surname": f"Test🙂{suf}"}, True, "Emoji"),
        MatrixScenario("surname_len_max_64", page_obj.SURNAME_INPUT, {"surname": surname_max}, True, "最大长度 64"),
        MatrixScenario("surname_len_over_65", page_obj.SURNAME_INPUT, {"surname": surname_over}, False, "超长 65", require_frontend_error_evidence=True),
    ]

    for sc in scenarios:
        run_matrix_case(auth_page, page_obj, baseline, sc)

    logger.end(success=True)

