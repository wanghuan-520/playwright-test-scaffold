# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Analyzer
# ═══════════════════════════════════════════════════════════════
"""
页面分析器 - 自动分析页面结构和元素
使用Playwright获取页面快照，识别可交互元素
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageElement:
    """页面元素"""
    selector: str
    tag: str
    type: str  # input, button, link, select, etc.
    text: str = ""
    placeholder: str = ""
    name: str = ""
    id: str = ""
    role: str = ""
    required: bool = False
    disabled: bool = False
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class PageInfo:
    """页面信息"""
    url: str
    title: str
    page_type: str  # LOGIN, FORM, LIST, DETAIL, DASHBOARD, SETTINGS
    elements: List[PageElement] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    navigation: List[Dict] = field(default_factory=list)


