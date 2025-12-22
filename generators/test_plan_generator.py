# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator (Coordinator)
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 协调器
"""

from pathlib import Path
from generators.page_types import PageInfo
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
        """生成测试计划"""
        logger.info(f"生成测试计划: {page_info.url}")
        
        sections = [
            self.formatter._header(page_info),
            self.formatter._overview(page_info),
            self.formatter._element_mapping(page_info),
            self.formatter._test_cases(page_info),
            self.formatter._test_data(page_info),
            self.formatter._page_object_skeleton(page_info),
            self.formatter._notes(page_info),
        ]
        
        return "\n\n".join(sections)
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION GENERATORS
    # ═══════════════════════════════════════════════════════════════
    

