"""
Profile Settings - P1 Email Validation Matrix
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
@allure.story("P1 - Email Validation Matrix")
@allure.description(
    """
测试点（email）：
- 必填：空 / 纯空白应被前端拦截（不发 profileUpdate）且有可见错误证据
- 格式：缺少 @ / 缺少 TLD / TLD=1 / 空格 / local 中文等典型非法形态
- 正常：普通邮箱 / plus / 子域名 / 最小合法形态（a@b.co）
- 长度：最大 256 / 超长 257
- 前后端一致性：选取部分非法形态（例如缺少 @）同时要求后端也 reject（避免“前端漏拦截”）
- 证据：每个场景 2 张关键截图（filled / result）
"""
)
def test_p1_profile_email_validation_matrix(profile_settings):
    logger = TestLogger("test_p1_profile_email_validation_matrix")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    suf = rand_suffix(auth_page)

    assert re.match(AbpUserConsts.EmailPattern, "a@b.co"), "sanity: AbpUserConsts.EmailPattern expects TLD>=2"

    domain = "example.com"
    fixed = f"@{domain}"
    local_max = max(1, AbpUserConsts.MaxEmailLength - len(fixed))
    suf_short = re.sub(r"\\D+", "", suf)[:10] or suf[:10]
    base_local = suf_short
    email_max = ((base_local + ("a" * (local_max + 20)))[:local_max]) + fixed
    email_over = ((base_local + ("b" * (local_max + 21)))[: (local_max + 1)]) + fixed

    scenarios = [
        MatrixScenario("email_required_empty", page_obj.EMAIL_INPUT, {"email": ""}, False, "必填", require_frontend_error_evidence=True),
        MatrixScenario("email_required_whitespace", page_obj.EMAIL_INPUT, {"email": "   "}, False, "必填/格式", require_frontend_error_evidence=True),
        MatrixScenario("email_bad_no_at", page_obj.EMAIL_INPUT, {"email": f"user{suf}.example.com"}, False, "缺少 @", require_frontend_error_evidence=True, require_backend_reject=True),
        MatrixScenario("email_bad_no_tld", page_obj.EMAIL_INPUT, {"email": f"user{suf}@example"}, False, "缺少顶级域名", require_frontend_error_evidence=True),
        MatrixScenario("email_bad_tld_1", page_obj.EMAIL_INPUT, {"email": f"user{suf}@example.c"}, False, "TLD 仅 1 位", require_frontend_error_evidence=True),
        MatrixScenario("email_bad_space", page_obj.EMAIL_INPUT, {"email": f"user {suf}@example.com"}, False, "包含空格", require_frontend_error_evidence=True),
        MatrixScenario("email_bad_cn", page_obj.EMAIL_INPUT, {"email": f"测试{suf}@example.com"}, False, "local 中文（默认正则不允许）", require_frontend_error_evidence=True),
        MatrixScenario("email_ok_normal", page_obj.EMAIL_INPUT, {"email": f"u_{suf}@testmail.com"}, True, "普通邮箱"),
        MatrixScenario("email_ok_plus", page_obj.EMAIL_INPUT, {"email": f"test+tag_{suf}@sub.domain.org"}, True, "plus/subdomain"),
        MatrixScenario("email_ok_min", page_obj.EMAIL_INPUT, {"email": "a@b.co"}, True, "最小合法形态"),
        MatrixScenario("email_len_max_256", page_obj.EMAIL_INPUT, {"email": email_max}, True, "最大长度 256"),
        MatrixScenario("email_len_over_257", page_obj.EMAIL_INPUT, {"email": email_over}, False, "超长 257", require_frontend_error_evidence=True),
    ]

    for sc in scenarios:
        run_matrix_case(auth_page, page_obj, baseline, sc)

    logger.end(success=True)

