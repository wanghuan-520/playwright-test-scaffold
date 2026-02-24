"""
Rule-compliant test plan helper functions.
"""

from __future__ import annotations

from urllib.parse import urlparse

from generators.page_types import PageElement, PageInfo
from generators.utils import requires_auth


def overview_lines(page_info: PageInfo) -> list[str]:
    url = (page_info.url or "").lower()
    if "change-password" in url or "password" in url:
        return [
            "进入页面并确认关键表单可见",
            "输入当前密码 / 新密码 / 确认新密码",
            "提交修改并观察成功/失败反馈（toast/表单错误/跳转）",
        ]
    if page_info.page_type == "SETTINGS":
        return ["进入设置页", "修改配置项", "保存并验证结果"]
    return ["进入页面", "完成主要交互", "验证可观察结果（UI 状态/业务结果）"]


def risk_lines(page_info: PageInfo) -> list[str]:
    url = (page_info.url or "").lower()
    risks: list[str] = []
    if requires_auth(page_info.page_type):
        risks.append("鉴权/权限：未登录或权限不足时的跳转与提示必须正确")
    if "password" in url:
        risks.extend(
            [
                "敏感信息：密码输入/错误提示不能泄露策略细节",
                "安全性：防 XSS/注入，避免把用户输入当作 HTML 执行",
                "不可逆/影响面：修改密码可能导致会话失效、影响后续登录",
            ]
        )
    if not risks:
        risks.append("稳定性：定位器漂移/异步加载导致 flaky")
    return risks


def locator_suggestion(e: PageElement) -> tuple[str, str]:
    txt = (e.text or "").strip()
    if e.type == "button" and txt:
        return "role/name", f'page.get_by_role("button", name="{txt}")'
    if e.type == "link" and txt:
        return "role/linkText", f'page.get_by_role("link", name="{txt}")'
    if e.role:
        return "role", f'page.get_by_role("{e.role}")'
    return "css", f'page.locator("{e.selector}")'


def semantic_hint(e: PageElement) -> str:
    key = " ".join([(e.name or ""), (e.id or ""), (e.placeholder or ""), (e.text or "")]).lower()
    if e.type == "input" and (e.attributes.get("type") or "").lower() == "password":
        if "current" in key or "old" in key:
            return "当前密码"
        if "confirm" in key or "repeat" in key:
            return "确认新密码"
        if "new" in key:
            return "新密码"
        return "密码输入"
    if e.type == "button":
        if "save" in key or "submit" in key or "confirm" in key:
            return "提交/保存"
        return "按钮操作"
    if e.type == "link":
        return "导航/跳转"
    return "表单字段/交互"


def checkpoints(e: PageElement) -> str:
    if e.type == "input":
        pts = ["可输入", "可清空", "校验提示（必填/格式/长度）"]
        if (e.attributes.get("type") or "").lower() == "password":
            pts.append("mask 显示/不回显明文")
        return " / ".join(pts)
    if e.type == "button":
        pts = ["可点击", "loading/禁用态", "触发结果（toast/错误提示/跳转）"]
        return " / ".join(pts)
    return "可见 / 可交互 / 行为正确"


def element_mapping_table(page_info: PageInfo, *, auth_required: bool) -> str:
    rows = []
    for e in (page_info.elements or []):
        strategy, locator = locator_suggestion(e)
        rows.append(
            "| {t} | {d} | {biz} | {st} | `{loc}` | {chk} | {dep} |".format(
                t=e.type or "-",
                d=(e.text or e.placeholder or e.name or e.id or "-").strip()[:60] or "-",
                biz=semantic_hint(e),
                st=strategy,
                loc=locator,
                chk=checkpoints(e),
                dep="需要登录态" if auth_required else "无",
            )
        )
    if not rows:
        rows.append("| - | - | - | - | - | - | - |")
    return "\n".join(
        [
            "| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |",
            "|---------|----------|----------|----------|--------|----------|----------|",
            *rows,
        ]
    )


def pom_skeleton(page_info: PageInfo, *, class_name: str) -> str:
    return "\n".join(
        [
            "from core.base_page import BasePage",
            "",
            "# ============================================================",
            f"# 页面对象：{class_name}",
            "# - 目标：封装稳定定位器与业务操作",
            "# - 原则：短小、直白、少分支",
            "# ============================================================",
            f"class {class_name}(BasePage):",
            "    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）",
            "    # CURRENT_PASSWORD_INPUT = ...",
            "    # NEW_PASSWORD_INPUT = ...",
            "    # CONFIRM_PASSWORD_INPUT = ...",
            "    # SUBMIT_BUTTON = ...",
            "",
            "    def navigate(self) -> None:",
            f"        self.goto(\"{page_info.url}\")",
            "",
            "    def is_loaded(self) -> bool:",
            "        # 以关键元素作为“已加载”判定",
            "        return True",
            "",
            "    # --------------------------------------------------------",
            "    # 业务动作（示例）",
            "    # --------------------------------------------------------",
            "    def submit_change_password(self, current_pwd: str, new_pwd: str, confirm_pwd: str) -> None:",
            "        # TODO: 填写并提交；失败时保留截图与上下文（证据链）",
            "        pass",
        ]
    )


def test_data_json(page_info: PageInfo) -> dict:
    url = (page_info.url or "").lower()
    if "password" in url:
        return {
            "valid": [
                {
                    "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                    "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                }
            ],
            "invalid": [
                {
                    "case": "missing_current_password",
                    "currentPassword": "",
                    "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                },
                {
                    "case": "wrong_current_password",
                    "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD_WRONG",
                    "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                },
                {
                    "case": "mismatch_confirm_password",
                    "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                    "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    "confirmNewPasswordLiteral": "__DIFFERENT_FROM_NEW__",
                },
            ],
            "boundary": [
                {
                    "case": "new_password_min_minus_1",
                    "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                    "newPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                    "confirmNewPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                },
                {
                    "case": "new_password_max_plus_1",
                    "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                    "newPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                    "confirmNewPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                },
            ],
        }
    return {
        "valid": [{"field1": "value1", "field2": "value2"}],
        "invalid": [{"field1": "", "field2": "invalid"}],
        "boundary": [{"field1": "min", "field2": "max"}],
    }


def implementation_suggestions(*, slug: str, class_name: str) -> str:
    module = (slug.split("_")[0] or "admin").strip()
    return "\n".join(
        [
            "### 5.1 页面类实现",
            f"- 建议 PageObject：`pages/{slug}_page.py`（类名 `{class_name}`，继承 `core/base_page.py:BasePage`）",
            "- 把“业务动作”封装成方法（不要在测试里散落 click/fill）",
            "- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）",
            "",
            "### 5.2 测试类实现",
            f"- 建议测试目录：`tests/{module}/{slug}/` 或对齐现有 suite 目录",
            "- 用 pytest 标记分层（@smoke/@p0/@p1/@security）",
            "- 数据驱动（valid/invalid/boundary）减少重复代码",
            "",
            "### 5.3 配置建议",
            "- 若需要：在 `config/project.yaml` 补充 base_url/账号策略",
            "- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检",
        ]
    )
