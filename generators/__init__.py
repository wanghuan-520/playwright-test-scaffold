# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Generators Module
# ═══════════════════════════════════════════════════════════════

from generators.page_analyzer import PageAnalyzer
from generators.page_types import PageElement, PageInfo
from generators.test_plan_generator import TestPlanGenerator
from generators.test_code_generator import TestCodeGenerator

# 可选分析器（某些精简版本脚手架未包含）
try:
    from generators.mcp_page_analyzer import MCPPageAnalyzer  # type: ignore
except Exception:  # pragma: no cover
    MCPPageAnalyzer = None  # type: ignore

try:
    from generators.smart_page_analyzer import SmartPageAnalyzer  # type: ignore
except Exception:  # pragma: no cover
    SmartPageAnalyzer = None  # type: ignore

__all__ = [
    'PageAnalyzer', 
    'PageElement', 
    'PageInfo', 
    'TestPlanGenerator', 
    'TestCodeGenerator'
]

if MCPPageAnalyzer is not None:
    __all__.append('MCPPageAnalyzer')
if SmartPageAnalyzer is not None:
    __all__.append('SmartPageAnalyzer')
