"""
Account/Login - Known Product Bugs (xfail)

目的：
- 把"确定是产品缺陷"的场景从主矩阵中剥离出来，避免全量回归红到看不见真实回归。
- 保留 Allure step + 截图证据，方便产品定位。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pytest  # type: ignore


@dataclass(frozen=True)
class KnownBug:
    """
    轻量缺陷台账条目（本文件是 Account/Login 的"权威缺陷簿"）。

    设计原则：
    - 缺陷描述只写一次
    - 各测试文件只引用 bug_id，避免 reason 文案 drift
    """

    bug_id: str
    title: str
    detail: str


# ============================================================
# Bug IDs (Login)
# ============================================================

BUG_LOGIN_LOCKOUT_NO_MESSAGE = "LOGIN-001"
BUG_LOGIN_INJECTION_500 = "LOGIN-002"


BUGS: Dict[str, KnownBug] = {
    BUG_LOGIN_LOCKOUT_NO_MESSAGE: KnownBug(
        bug_id=BUG_LOGIN_LOCKOUT_NO_MESSAGE,
        title="多次登录失败后锁定账号，但错误消息不够明确",
        detail="期望：应显示'账号已锁定，请等待X分钟后重试'，而非通用错误。",
    ),
    BUG_LOGIN_INJECTION_500: KnownBug(
        bug_id=BUG_LOGIN_INJECTION_500,
        title="Login 注入 payload 可能触发 500（Internal Server Error）",
        detail="覆盖字段×payload 矩阵；期望：不执行脚本、不弹 dialog、不进入致命错误页，且响应不得为 5xx。",
    ),
}


def bug_reason(bug_id: str, *, extra: str = "") -> str:
    b = BUGS.get(bug_id)
    if not b:
        return f"[{bug_id}] (unknown bug id)"
    suffix = f" | {extra.strip()}" if (extra or "").strip() else ""
    return f"[{b.bug_id}] {b.title}{suffix}"


def bug_xfail(bug_id: str, *, strict: bool = False, extra: str = ""):
    """
    统一创建 xfail 标记：测试文件里不要再写自由文本 reason。
    """
    return pytest.mark.xfail(reason=bug_reason(bug_id, extra=extra), strict=bool(strict))


# NOTE:
# - 本文件不再包含"可执行用例"，只做缺陷台账 + 工具函数。
# - 如需新增缺陷：加一个 BUG_ID + BUGS 条目，然后在用例里引用 bug_xfail(BUG_ID)。

