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
    # 是否需要登录态（可选字段：用于生成测试计划时更准确地表达前置条件）
    # - None: 未判定（旧数据兼容）
    # - True/False: 调用方（动态分析/爬站）给出的结论
    auth_required: Optional[bool] = None
    elements: List[PageElement] = field(default_factory=list)
    forms: List[Dict] = field(default_factory=list)
    navigation: List[Dict] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# JSON helpers (for MCP/CLI bridge)
# ═══════════════════════════════════════════════════════════════


def page_element_from_dict(d: Dict[str, Any]) -> PageElement:
    """
    从 dict 反序列化 PageElement。
    允许字段缺失：用默认值兜底，避免“格式升级”导致历史快照不可用。
    """
    return PageElement(
        selector=str(d.get("selector") or ""),
        tag=str(d.get("tag") or ""),
        type=str(d.get("type") or ""),
        text=str(d.get("text") or ""),
        placeholder=str(d.get("placeholder") or ""),
        name=str(d.get("name") or ""),
        id=str(d.get("id") or ""),
        role=str(d.get("role") or ""),
        required=bool(d.get("required") or False),
        disabled=bool(d.get("disabled") or False),
        attributes=dict(d.get("attributes") or {}),
    )


def page_info_from_dict(d: Dict[str, Any]) -> PageInfo:
    """
    从 dict 反序列化 PageInfo。
    """
    elements_raw = d.get("elements") or []
    elements = [page_element_from_dict(x) for x in elements_raw if isinstance(x, dict)]
    return PageInfo(
        url=str(d.get("url") or ""),
        title=str(d.get("title") or ""),
        page_type=str(d.get("page_type") or "FORM"),
        auth_required=(d.get("auth_required") if isinstance(d.get("auth_required"), bool) else None),
        elements=elements,
        forms=list(d.get("forms") or []),
        navigation=list(d.get("navigation") or []),
    )


