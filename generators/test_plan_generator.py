# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator (Coordinator)
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 协调器

说明：
- 本仓库的 `.cursor/rules/ui-test-plan-generator.mdc` 约束了测试计划的结构与落盘路径；
- 这里输出的 Markdown 以“可落地、可追溯、可执行”为目标，优先写清楚：证据链、定位策略、用例优先级与风险。
"""

from __future__ import annotations

import json
from datetime import datetime

from generators.page_types import PageInfo, PageElement
from generators.utils import (
    get_page_name_from_url,
    get_file_name_from_url,
    to_class_name,
    requires_auth,
)
from urllib.parse import urlparse
from generators.test_plan_formatter import TestPlanFormatter
from generators.test_plan_scenarios import TestPlanScenarios
from utils.logger import get_logger

logger = get_logger(__name__)


class TestPlanGenerator:
    """测试计划生成器 - 协调器"""
    
    def __init__(self):
        """初始化子生成器"""
        self.formatter = TestPlanFormatter()
        self.scenarios = TestPlanScenarios()
    
    def generate(self, page_info: PageInfo) -> str:
        """
        生成测试计划（对齐 ui-test-plan-generator.mdc）。

        注意：
        - 证据链目录按约定计算：docs/test-plans/artifacts/<slug>/
          实际写入由调用方负责（当前推荐手动流程，不依赖历史一键入口）。
        """
        logger.info(f"生成测试计划: {page_info.url}")
        return self._generate_rule_compliant(page_info)

    # ═══════════════════════════════════════════════════════════════
    # Rule-compliant generator (ui-test-plan-generator.mdc)
    # ═══════════════════════════════════════════════════════════════

    def _generate_rule_compliant(self, page_info: PageInfo) -> str:
        slug = get_file_name_from_url(page_info.url)
        page_name = get_page_name_from_url(page_info.url)
        class_name = f"{to_class_name(page_name)}Page"
        # 认证前置：优先使用动态分析给出的结论（更接近真实环境）
        auth_required = (
            page_info.auth_required
            if isinstance(getattr(page_info, "auth_required", None), bool)
            else requires_auth(page_info.page_type)
        )
        need_auth = "是" if auth_required else "否"

        overview = self._overview_lines(page_info)
        risk = self._risk_lines(page_info)
        mapping = self._element_mapping_table(page_info, auth_required=auth_required)
        pom = self._pom_skeleton(page_info, class_name=class_name)
        cases = self._cases_block(page_info)
        data = self._test_data_json(page_info)
        impl = self._implementation_suggestions(page_info, slug=slug, class_name=class_name)

        return "\n".join(
            [
                f"# {page_name} UI 自动化测试计划",
                "",
                "## 0. 生成信息（用于可追溯）",
                f"- **URL**: `{page_info.url}`",
                f"- **slug**: `{slug}`",
                f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **是否需要登录态**: {need_auth}",
                f"- **证据链目录**: `docs/test-plans/artifacts/{slug}/`",
                "",
                "## 1. 页面概述",
                f"- **页面类型**: {page_info.page_type}",
                "- **主要功能（用户任务流）**:",
                *[f"  - {x}" for x in overview],
                "- **风险点**:",
                *[f"  - {x}" for x in risk],
                "- **测试优先级**: 高（涉及权限/敏感操作/不可逆风险的页面默认 P0 覆盖）",
                "",
                "## 2. 页面元素映射",
                "### 2.1 关键元素识别",
                mapping,
                "",
                "### 2.2 页面对象设计（骨架）",
                "```python",
                *pom.splitlines(),
                "```",
                "",
                "## 3. 测试用例设计",
                cases,
                "",
                "## 4. 测试数据设计（JSON）",
                "```json",
                json.dumps(data, indent=2, ensure_ascii=False),
                "```",
                "",
                "## 5. 自动化实现建议（对齐本仓库）",
                impl,
                "",
                "## 6. 执行计划",
                "- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例",
                "- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）",
                "- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）",
            ]
        ).strip() + "\n"

    def _overview_lines(self, page_info: PageInfo) -> list[str]:
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

    def _risk_lines(self, page_info: PageInfo) -> list[str]:
        url = (page_info.url or "").lower()
        risks = []
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

    def _locator_suggestion(self, e: PageElement) -> tuple[str, str]:
        """
        输出：定位策略、定位器（优先 role/name，其次 css 兜底）
        """
        txt = (e.text or "").strip()
        if e.type == "button" and txt:
            return "role/name", f'page.get_by_role("button", name="{txt}")'
        if e.type == "link" and txt:
            return "role/linkText", f'page.get_by_role("link", name="{txt}")'
        if e.role:
            return "role", f'page.get_by_role("{e.role}")'
        return "css", f'page.locator("{e.selector}")'

    def _semantic_hint(self, e: PageElement) -> str:
        """
        粗略给出业务语义（用于计划，不参与执行）。
        """
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

    def _checkpoints(self, e: PageElement) -> str:
        if e.type == "input":
            pts = ["可输入", "可清空", "校验提示（必填/格式/长度）"]
            if (e.attributes.get("type") or "").lower() == "password":
                pts.append("mask 显示/不回显明文")
            return " / ".join(pts)
        if e.type == "button":
            pts = ["可点击", "loading/禁用态", "触发结果（toast/错误提示/跳转）"]
            return " / ".join(pts)
        return "可见 / 可交互 / 行为正确"

    def _element_mapping_table(self, page_info: PageInfo, *, auth_required: bool) -> str:
        rows = []
        for e in (page_info.elements or []):
            strategy, locator = self._locator_suggestion(e)
            desc = self._semantic_hint(e)
            rows.append(
                "| {t} | {d} | {biz} | {st} | `{loc}` | {chk} | {dep} |".format(
                    t=e.type or "-",
                    d=(e.text or e.placeholder or e.name or e.id or "-").strip()[:60] or "-",
                    biz=desc,
                    st=strategy,
                    loc=locator,
                    chk=self._checkpoints(e),
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

    def _pom_skeleton(self, page_info: PageInfo, *, class_name: str) -> str:
        # 只给骨架：避免把执行细节塞进计划
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

    def _cases_block(self, page_info: PageInfo) -> str:
        url = (page_info.url or "").strip()
        path = (urlparse(url).path or "/").lower()

        # 账号建议（只写 email，不写密码）
        # - 普通账号：个人设置/工作流等
        # - 管理员账号：用户/角色/设置等 admin-only 页面
        account_hint = [
            "- **账号建议**:",
            "  - **普通账号 email（示例）**: `hayleetest1@test.com`（用于个人设置/Workflow 等）",
            "  - **管理员账号 email（示例）**: `admin-test01@test.com`（用于 Users/Roles/Settings 等管理页）",
            "  - **密码**: 运行期由环境变量/账号池提供；计划与任何落盘文件禁止写入密码",
            "",
        ]

        base_p0 = [
            "- **TC001**: 页面加载",
            "  - **标签**: [@smoke @p0]",
            "  - **前置条件**: 已登录（若需要）",
            "  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见",
            "  - **预期结果**: 页面可用且无阻塞错误",
            "  - **断言层级**: UI 状态",
            "  - **优先级**: 高",
            "",
        ]

        # ──────────────────────────────────────────────────────────
        # Account pages (backend)
        # ──────────────────────────────────────────────────────────
        if path.startswith("/account/login"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 登录成功（有效凭证）",
                "  - **标签**: [@p0 @auth]",
                "  - **前置条件**: 有效账号（通过账号池/环境变量注入）",
                "  - **测试步骤**: 输入用户名/邮箱 + 密码 → 点击 Login → 等待跳转",
                "  - **预期结果**: 登录成功并回跳到前端域（`https://localhost:3000`）或进入授权后的目标页",
                "  - **断言层级**: UI 状态 + URL/可观测用户菜单",
                "  - **优先级**: 高",
                "",
                "- **TC003**: 登录失败（错误密码）",
                "  - **标签**: [@p0 @negative]",
                "  - **测试步骤**: 输入正确用户名 + 错误密码 → Login",
                "  - **预期结果**: 显示错误提示；不会建立前端登录态",
                "  - **断言层级**: UI 可观测错误 + 仍停留登录页",
                "  - **优先级**: 高",
                "",
                "- **TC004**: 必填校验（用户名/密码为空）",
                "  - **标签**: [@p1 @validation]",
                "  - **测试步骤**: 清空用户名或密码 → Login",
                "  - **预期结果**: 表单显示必填提示或阻止提交",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 防账号枚举（错误提示不区分“用户不存在/密码错误”）",
                "  - **标签**: [@p1 @security]",
                "  - **测试步骤**: 分别用不存在账号/存在账号错误密码尝试登录",
                "  - **预期结果**: 错误提示保持同一风格，不泄露账号存在性",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        if path.startswith("/account/register"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 注册页字段可输入 + 提交按钮可用性",
                "  - **标签**: [@p0]",
                "  - **测试步骤**: 填写必填项（以页面可见标识为准）→ 提交",
                "  - **预期结果**: 成功注册或得到可诊断的校验提示（不出现 5xx）",
                "  - **优先级**: 高",
                "",
                "- **TC003**: Email 格式校验",
                "  - **标签**: [@p1 @validation]",
                "  - **测试步骤**: 输入非法 email（如缺少 @）→ 提交",
                "  - **预期结果**: 前端或后端拒绝并展示错误证据（字段 invalid/提示/4xx）",
                "  - **优先级**: 中",
                "",
                "- **TC004**: 密码策略矩阵（以后端 ABP 为真理源）",
                "  - **标签**: [@p1 @validation]",
                "  - **测试步骤**: 使用不满足策略的密码（缺数字/缺大写/太短等）→ 提交",
                "  - **预期结果**: 被拒绝；提示可观测；不落盘任何密码样例",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 注册失败不泄露敏感信息（错误体/提示不包含密码明文）",
                "  - **标签**: [@p1 @security]",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        if path.startswith("/account/forgotpassword"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 找回密码提交（存在/不存在账号都应给出同风格反馈）",
                "  - **标签**: [@p0]",
                "  - **测试步骤**: 输入 email → Submit",
                "  - **预期结果**: 显示“已发送邮件/若账号存在则发送”类提示；不泄露账号是否存在",
                "  - **优先级**: 高",
                "",
                "- **TC003**: Email 格式校验",
                "  - **标签**: [@p1 @validation]",
                "  - **测试步骤**: 输入非法 email → Submit",
                "  - **预期结果**: 可观测错误提示",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 防账号枚举（提示一致性）",
                "  - **标签**: [@p1 @security]",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        # ──────────────────────────────────────────────────────────
        # Admin / Settings / Users / Roles
        # ──────────────────────────────────────────────────────────
        if path.startswith("/admin/users/roles"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 角色列表可用（加载/空态/错误态）",
                "  - **标签**: [@p0]",
                "  - **前置条件**: 管理员登录",
                "  - **测试步骤**: 打开页面 → 等待列表区域渲染",
                "  - **预期结果**: 列表渲染成功（无 5xx / 无阻塞报错）",
                "  - **优先级**: 高",
                "",
                "- **TC003**: 未授权拦截",
                "  - **标签**: [@p1 @auth]",
                "  - **前置条件**: 未登录/非管理员账号",
                "  - **预期结果**: 被拦截或重定向到登录；不得展示管理数据",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        if path.startswith("/admin/users"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 用户列表加载",
                "  - **标签**: [@p0]",
                "  - **前置条件**: 管理员登录",
                "  - **测试步骤**: 打开页面 → 等待用户列表/表格区域渲染",
                "  - **预期结果**: 列表渲染成功（空态/加载态可接受，但不得 5xx）",
                "  - **优先级**: 高",
                "",
                "- **TC003**: 搜索过滤（Search...）",
                "  - **标签**: [@p1]",
                "  - **测试步骤**: 在 Search 输入框输入关键字 → 观察列表变化",
                "  - **预期结果**: 列表过滤结果可观测（行数变化/空态提示）",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 未授权拦截",
                "  - **标签**: [@p1 @security @auth]",
                "  - **前置条件**: 未登录/非管理员",
                "  - **预期结果**: 被拦截或重定向；不得暴露用户数据",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        if path.startswith("/admin/settings/feature-management"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: 打开 Feature Management 页",
                "  - **标签**: [@p0]",
                "  - **前置条件**: 管理员登录",
                "  - **测试步骤**: 打开页面 → 断言 Feature Management 标题/关键按钮可见",
                "  - **预期结果**: 页面可用；按钮可点击（不出现 5xx）",
                "  - **优先级**: 高",
                "",
                "- **TC003**: Manage Host Features 按钮行为",
                "  - **标签**: [@p1]",
                "  - **测试步骤**: 点击按钮 → 观察弹窗/跳转/加载状态（以实际为准）",
                "  - **预期结果**: 行为可观测且可关闭/可回退",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 未授权拦截",
                "  - **标签**: [@p1 @security @auth]",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        if path.startswith("/admin/settings"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: Settings Tab 切换（Emailing / Feature management）",
                "  - **标签**: [@p0]",
                "  - **前置条件**: 管理员登录",
                "  - **测试步骤**: 点击 Emailing → 点击 Feature management → 再切回",
                "  - **预期结果**: Tab 内容切换正确，状态不丢失（以实际为准）",
                "  - **优先级**: 高",
                "",
                "- **TC003**: Emailing 表单保存（最小修改）",
                "  - **标签**: [@p0]",
                "  - **测试步骤**: 修改一个非敏感字段（如 Display name）→ 保存（若存在 Save/提交行为）",
                "  - **预期结果**: 成功提示或可观测保存结果；不出现 5xx",
                "  - **优先级**: 高",
                "",
                "- **TC004**: Port 边界/类型校验（数字/范围）",
                "  - **标签**: [@p1 @validation]",
                "  - **测试步骤**: 输入非法端口（负数/非数字/超范围）→ 保存",
                "  - **预期结果**: 被拦截或后端拒绝；错误可观测",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 密码字段不回显明文",
                "  - **标签**: [@p1 @security]",
                "  - **预期结果**: 密码输入框为 password 类型；截图/日志不出现明文",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        # ──────────────────────────────────────────────────────────
        # Workflow / Home / Generic protected
        # ──────────────────────────────────────────────────────────
        if path.startswith("/workflow"):
            cases = [
                *account_hint,
                *base_p0,
                "- **TC002**: New Workflow 按钮可用",
                "  - **标签**: [@p0]",
                "  - **测试步骤**: 打开页面 → 点击 New Workflow（若存在）",
                "  - **预期结果**: 弹窗/跳转可观测；可关闭/可回退",
                "  - **优先级**: 高",
                "",
                "- **TC003**: Import Workflow 基础校验",
                "  - **标签**: [@p1]",
                "  - **测试步骤**: 点击 Import Workflow → 不选择文件直接提交（或取消）",
                "  - **预期结果**: 不崩溃；提示可观测",
                "  - **优先级**: 中",
                "",
                "- **TC-SEC-001**: 未登录可访问性（若页面支持匿名）/或强制登录拦截（以实际为准）",
                "  - **标签**: [@p1 @auth]",
                "  - **优先级**: 中",
            ]
            return "\n".join(["### 3.1 功能测试用例", *cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        # Password-like pages（保留已补充的改密用例）
        if "password" in path:
            # 复用历史逻辑：改密页面的核心矩阵
            base = [
                "- **TC001**: 页面加载",
                "  - **标签**: [@smoke @p0]",
                "  - **前置条件**: 已登录（若需要）",
                "  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见",
                "  - **预期结果**: 页面可用且无阻塞错误",
                "  - **断言层级**: UI 状态",
                "  - **优先级**: 高",
            ]
        pwd_cases = [
            "- **TC002**: 必填校验（未填当前密码）",
            "  - **标签**: [@p0 @validation]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 仅填写新密码/确认密码 → 提交",
            "  - **预期结果**: 当前密码出现必填提示；提交被阻止",
            "  - **断言层级**: UI 状态",
            "  - **优先级**: 高",
            "",
            "- **TC003**: 新密码与确认密码不一致",
            "  - **标签**: [@p0 @validation]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 填写当前密码 → 新密码/确认密码填不一致 → 提交",
            "  - **预期结果**: 提示不一致；不调用提交或提交失败可观测",
            "  - **断言层级**: UI 状态/可观察性（toast/接口）",
            "  - **优先级**: 高",
            "",
            "- **TC004**: 当前密码错误",
            "  - **标签**: [@p0 @exception]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 输入错误当前密码 → 输入合法新密码/确认 → 提交",
            "  - **预期结果**: 显示错误提示；密码不被修改",
                "  - **断言层级**: 业务结果/UI 提示",
            "  - **优先级**: 高",
            "",
                "- **TC005**: 修改成功（建议回滚）",
            "  - **标签**: [@p0]",
            "  - **前置条件**: 已登录；账号可用于修改密码",
                "  - **测试步骤**: 修改成功后立刻回滚到原密码（避免污染账号池）",
                "  - **预期结果**: 两次提交都成功且可观测",
            "  - **优先级**: 高",
        ]
        sec = [
                "- **TC-SEC-001**: 未登录访问拦截",
            "  - **标签**: [@p1 @auth]",
            "  - **前置条件**: 未登录",
                "  - **预期结果**: 重定向到登录或提示未授权",
            "  - **优先级**: 中",
            "",
                "- **TC-SEC-002**: XSS 输入不执行",
            "  - **标签**: [@p1 @security]",
                "  - **预期结果**: 不弹窗；输入不被当作 HTML 执行",
                "  - **优先级**: 中",
            ]
            return "\n".join(
                [
                    "### 3.1 功能测试用例",
                    *account_hint,
                    *base,
                    "",
                    *pwd_cases,
                    "",
                    "### 3.2 边界测试用例",
                    "",
                    "### 3.3 异常测试用例",
                    "",
                    *sec,
                ]
            )

        # Generic default
        generic = [
            *account_hint,
            *base_p0,
            "- **TC-SEC-001**: 未登录访问拦截（如页面受保护）",
            "  - **标签**: [@p1 @auth]",
            "  - **预期结果**: 跳转登录或提示未授权",
            "  - **优先级**: 中",
        ]
        return "\n".join(["### 3.1 功能测试用例", *generic, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

    def _test_data_json(self, page_info: PageInfo) -> dict:
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

    def _implementation_suggestions(self, page_info: PageInfo, *, slug: str, class_name: str) -> str:
        # 对齐仓库目录结构与命名惯例
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

    def _test_cases(self, page_info: PageInfo) -> str:
        """
        测试用例章节（来自 TestPlanScenarios）。
        
        说明：
        - formatter 负责“文档结构/排版”
        - scenarios 负责“具体用例内容”
        - 这里显式组合，避免 formatter 误持有 scenarios 的内部方法
        """
        cases = []

        cases.append("### 3.1 P0 - Critical Tests (核心功能)")
        cases.extend(self.scenarios._p0_tests(page_info))

        cases.append("\n### 3.2 P1 - High Priority Tests (重要功能)")
        cases.extend(self.scenarios._p1_tests(page_info))

        cases.append("\n### 3.3 P2 - Medium Priority Tests (一般功能)")
        cases.extend(self.scenarios._p2_tests(page_info))

        return f"""## 3. Test Cases

{chr(10).join(cases)}"""
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION GENERATORS
    # ═══════════════════════════════════════════════════════════════
    

