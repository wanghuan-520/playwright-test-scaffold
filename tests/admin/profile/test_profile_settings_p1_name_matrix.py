"""
Profile Settings - P1 Name Validation Matrix
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
@allure.story("P1 - Name Validation Matrix")
@allure.description(
    """
测试点（name，可选字段）：
- 可空：空 / 纯空白允许保存（按 ABP 默认）
- 字符集：英文、中文、常见特殊字符、Emoji（按 ABP 默认不限制字符集）
- 长度：最大 64 / 超长 65
- 证据：每个场景 2 张关键截图（filled / result）
"""
)
def test_p1_profile_name_validation_matrix(profile_settings):
    logger = TestLogger("test_p1_profile_name_validation_matrix")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    suf = rand_suffix(auth_page)

    max_len = AbpUserConsts.MaxNameLength
    name_max = "N" * max_len
    name_over = "O" * (max_len + 1)

    scenarios = [
        MatrixScenario("name_empty", page_obj.NAME_INPUT, {"name": ""}, True, "可空"),
        MatrixScenario("name_whitespace", page_obj.NAME_INPUT, {"name": "   "}, True, "可空/空白"),
        MatrixScenario("name_en", page_obj.NAME_INPUT, {"name": f"John_{suf}"}, True, "英文"),
        MatrixScenario("name_cn", page_obj.NAME_INPUT, {"name": f"中文{suf}"}, True, "中文允许（ABP 默认）"),
        MatrixScenario("name_mix_special", page_obj.NAME_INPUT, {"name": f"O'Brien-{suf}!@#"}, True, "特殊字符允许（ABP 默认）"),
        MatrixScenario("name_emoji", page_obj.NAME_INPUT, {"name": f"User🙂{suf}"}, True, "Emoji"),
        MatrixScenario("name_len_max_64", page_obj.NAME_INPUT, {"name": name_max}, True, "最大长度 64"),
        MatrixScenario("name_len_over_65", page_obj.NAME_INPUT, {"name": name_over}, False, "超长 65", require_frontend_error_evidence=True),
    ]

    for sc in scenarios:
        run_matrix_case(auth_page, page_obj, baseline, sc)

    logger.end(success=True)

