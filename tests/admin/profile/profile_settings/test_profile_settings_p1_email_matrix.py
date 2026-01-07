"""
Profile Settings - P1 Email Validation Matrix

优化说明：
- 将原 for 循环改为 pytest.mark.parametrize，每个场景独立执行
- 可充分利用 pytest-xdist 并行能力，显著提升速度
"""

from __future__ import annotations

import re

import allure  # pyright: ignore[reportMissingImports]
import pytest  # pyright: ignore[reportMissingImports]

from utils.logger import TestLogger
from tests.admin.profile._helpers import AbpUserConsts
from tests.admin.profile._matrix_helpers import MatrixScenario, rand_suffix, run_matrix_case


# ═══════════════════════════════════════════════════════════════
# 参数化场景列表
# ═══════════════════════════════════════════════════════════════
def _email_scenarios():
    """
    生成参数化场景：13个场景，包含完整边界值测试
    """
    # 静态验证
    assert re.match(AbpUserConsts.EmailPattern, "a@b.co"), "sanity: AbpUserConsts.EmailPattern expects TLD>=2"
    
    # 计算最大长度邮箱
    domain = "example.com"
    fixed = f"@{domain}"
    local_max = max(1, AbpUserConsts.MaxEmailLength - len(fixed))
    # 使用静态前缀（suf会在test中动态生成）
    base_local = "a" * min(10, local_max)
    email_max_minus_1 = (base_local + ("a" * (local_max + 20)))[:(local_max - 1)] + fixed
    email_max = (base_local + ("a" * (local_max + 20)))[:local_max] + fixed
    email_max_plus_1 = (base_local + ("b" * (local_max + 21)))[:(local_max + 1)] + fixed
    
    scenarios = [
        ("email_required_empty", "EMAIL_INPUT", {"email": ""}, False, "必填", False, True, False),
        ("email_required_whitespace", "EMAIL_INPUT", {"email": "   "}, False, "必填/格式", False, True, False),
        ("email_bad_no_at", "EMAIL_INPUT", {"email": "user.example.com"}, False, "缺少 @", True, True, True),
        ("email_bad_no_tld", "EMAIL_INPUT", {"email": "user@example"}, False, "缺少顶级域名", True, True, False),
        ("email_bad_tld_1", "EMAIL_INPUT", {"email": "user@example.c"}, False, "TLD 仅 1 位", True, True, False),
        ("email_bad_space", "EMAIL_INPUT", {"email": "user name@example.com"}, False, "包含空格", True, True, False),
        ("email_bad_cn", "EMAIL_INPUT", {"email": "测试@example.com"}, False, "local 中文（默认正则不允许）", True, True, False),
        ("email_ok_normal", "EMAIL_INPUT", {"email": "u_@testmail.com"}, True, "普通邮箱", True, False, False),
        ("email_ok_plus", "EMAIL_INPUT", {"email": "test+tag_@sub.domain.org"}, True, "plus/subdomain", True, False, False),
        ("email_ok_min", "EMAIL_INPUT", {"email": "a@b.co"}, True, "最小合法形态", False, False, False),
        ("email_len_max_minus_1", "EMAIL_INPUT", {"email": email_max_minus_1}, True, "最大长度-1（255）应成功", False, False, False),
        ("email_len_max_256", "EMAIL_INPUT", {"email": email_max}, True, "最大长度（256）应成功", False, False, False),
        ("email_len_max_plus_1", "EMAIL_INPUT", {"email": email_max_plus_1}, False, "超长（257）应失败", False, False, False),
    ]
    
    params = []
    for case_name, selector_attr, patch, should_save, note, need_suffix, require_frontend_error, require_backend_reject in scenarios:
        params.append(
            pytest.param(
                case_name,
                selector_attr,
                patch,
                should_save,
                note,
                need_suffix,
                require_frontend_error,
                require_backend_reject,
                id=case_name,
            )
        )
    return params


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
- 前后端一致性：选取部分非法形态（例如缺少 @）同时要求后端也 reject（避免"前端漏拦截"）
- 证据：每个场景 2 张关键截图（filled / result）

优化：使用参数化测试，每个场景独立执行，可并行
"""
)
@pytest.mark.parametrize(
    "case_name,selector_attr,patch,should_save,note,need_suffix,require_frontend_error,require_backend_reject",
    _email_scenarios(),
)
def test_p1_profile_email_validation_matrix(
    profile_settings,
    case_name: str,
    selector_attr: str,
    patch: dict,
    should_save: bool,
    note: str,
    need_suffix: bool,
    require_frontend_error: bool,
    require_backend_reject: bool,
):
    logger = TestLogger(f"test_p1_profile_email_validation_matrix[{case_name}]")
    logger.start()

    auth_page, page_obj, baseline = profile_settings
    
    # 动态添加 suffix（如果需要）
    if need_suffix:
        suf = rand_suffix(auth_page)
        patch_copy = {}
        for k, v in patch.items():
            if isinstance(v, str) and ("@" in v):
                # email 格式：在 @ 前添加 suffix
                parts = v.split("@")
                patch_copy[k] = f"{parts[0]}{suf}@{parts[1]}"
            elif isinstance(v, str):
                patch_copy[k] = f"{v}{suf}"
            else:
                patch_copy[k] = v
        patch = patch_copy
    
    # 获取 selector
    selector = getattr(page_obj, selector_attr)
    
    # 构造 MatrixScenario 并执行
    scenario = MatrixScenario(
        case_name=case_name,
        selector=selector,
        patch=patch,
        should_save=should_save,
        note=note,
        require_frontend_error_evidence=require_frontend_error,
        require_backend_reject=require_backend_reject,
        allow_taken_conflict=False,
    )
    
    run_matrix_case(auth_page, page_obj, baseline, scenario)

    logger.end(success=True)
