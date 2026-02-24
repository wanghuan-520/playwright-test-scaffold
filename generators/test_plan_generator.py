# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator (Coordinator)
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 协调器。

说明：
- 保留原有入口 `TestPlanGenerator.generate()`，对外行为不变；
- 规则细节拆分到 helper 模块，降低单文件复杂度。
"""

from __future__ import annotations

import json
from datetime import datetime

from generators.page_types import PageElement, PageInfo
from generators.test_plan_formatter import TestPlanFormatter
from generators.test_plan_rule_cases import cases_block
from generators.test_plan_rule_helpers import (
    checkpoints,
    element_mapping_table,
    implementation_suggestions,
    locator_suggestion,
    overview_lines,
    pom_skeleton,
    risk_lines,
    semantic_hint,
    test_data_json,
)
from generators.test_plan_scenarios import TestPlanScenarios
from generators.utils import get_file_name_from_url, get_page_name_from_url, requires_auth, to_class_name
from utils.logger import get_logger

logger = get_logger(__name__)


class TestPlanGenerator:
    """测试计划生成器 - 协调器。"""

    def __init__(self):
        self.formatter = TestPlanFormatter()
        self.scenarios = TestPlanScenarios()

    def generate(self, page_info: PageInfo) -> str:
        logger.info(f"生成测试计划: {page_info.url}")
        return self._generate_rule_compliant(page_info)

    def _generate_rule_compliant(self, page_info: PageInfo) -> str:
        slug = get_file_name_from_url(page_info.url)
        page_name = get_page_name_from_url(page_info.url)
        class_name = f"{to_class_name(page_name)}Page"
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

    # ═══════════════════════════════════════════════════════════════
    # Wrappers (保留原私有接口，避免潜在调用方破坏)
    # ═══════════════════════════════════════════════════════════════

    def _overview_lines(self, page_info: PageInfo) -> list[str]:
        return overview_lines(page_info)

    def _risk_lines(self, page_info: PageInfo) -> list[str]:
        return risk_lines(page_info)

    def _locator_suggestion(self, e: PageElement) -> tuple[str, str]:
        return locator_suggestion(e)

    def _semantic_hint(self, e: PageElement) -> str:
        return semantic_hint(e)

    def _checkpoints(self, e: PageElement) -> str:
        return checkpoints(e)

    def _element_mapping_table(self, page_info: PageInfo, *, auth_required: bool) -> str:
        return element_mapping_table(page_info, auth_required=auth_required)

    def _pom_skeleton(self, page_info: PageInfo, *, class_name: str) -> str:
        return pom_skeleton(page_info, class_name=class_name)

    def _cases_block(self, page_info: PageInfo) -> str:
        return cases_block(page_info)

    def _test_data_json(self, page_info: PageInfo) -> dict:
        return test_data_json(page_info)

    def _implementation_suggestions(self, page_info: PageInfo, *, slug: str, class_name: str) -> str:
        _ = page_info
        return implementation_suggestions(slug=slug, class_name=class_name)
