# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Generator Utilities
# ═══════════════════════════════════════════════════════════════
"""
生成器公共工具模块 - 提取重复的辅助函数

职责：
- 命名转换（snake_case, PascalCase, CONSTANT_CASE）
- 页面/元素名称提取
- 测试用例前缀生成
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from generators.page_types import PageInfo, PageElement


# ═══════════════════════════════════════════════════════════════
# NAMING CONVERTERS
# ═══════════════════════════════════════════════════════════════

def to_snake_case(name: str) -> str:
    """
    转换为蛇形命名 (snake_case)
    
    Examples:
        "Login Page" -> "login_page"
        "user-name" -> "user_name"
        "TestCase" -> "testcase"
    """
    # 移除特殊字符
    name = re.sub(r'[^\w\s-]', '', name)
    # 空格/横线转下划线
    return re.sub(r'[\s-]+', '_', name).lower()


def to_class_name(name: str) -> str:
    """
    转换为类名 (PascalCase)
    
    Examples:
        "login page" -> "LoginPage"
        "user-profile" -> "UserProfile"
    """
    return "".join(word.title() for word in re.split(r'[\s_-]+', name))


def to_constant_name(base: str, suffix: str = "") -> str:
    """
    转换为常量名 (CONSTANT_CASE)
    
    Args:
        base: 基础名称
        suffix: 后缀 (如 "_INPUT", "_BUTTON")
    
    Examples:
        ("username", "_INPUT") -> "USERNAME_INPUT"
        ("submit btn", "_BUTTON") -> "SUBMIT_BTN_BUTTON"
    """
    # 清理特殊字符
    base = re.sub(r'[^\w\s]', '', base)
    # 转大写，限制长度
    base = re.sub(r'[\s-]+', '_', base).upper()[:30]
    return f"{base}{suffix}"


# ═══════════════════════════════════════════════════════════════
# PAGE INFO EXTRACTORS
# ═══════════════════════════════════════════════════════════════

def get_page_name_from_url(url: str) -> str:
    """
    从URL提取页面名称 (Title Case)
    
    Examples:
        "https://example.com/login" -> "Login"
        "https://example.com/user-profile" -> "User Profile"
        "https://example.com/" -> "Home"
    """
    path = url.split("?")[0].rstrip("/")
    parts = path.split("/")
    name = parts[-1] if parts[-1] else "home"
    return name.replace("-", " ").replace("_", " ").title()


def get_file_name_from_url(url: str) -> str:
    """
    从URL提取文件名 (snake_case)
    
    Examples:
        "https://example.com/login" -> "login"
        "https://example.com/user-profile" -> "user_profile"
    """
    path = url.split("?")[0].rstrip("/")
    name = path.split("/")[-1] or "home"
    return to_snake_case(name)


def get_tc_prefix_from_url(url: str) -> str:
    """
    从URL生成测试用例前缀 (大写前4字符)
    
    Examples:
        "https://example.com/login" -> "LOGI"
        "https://example.com/user-profile" -> "USER"
    """
    name = get_page_name_from_url(url)
    return name.upper().replace(" ", "")[:4]


def extract_url_path(url: str) -> str:
    """
    提取URL路径部分
    
    Examples:
        "https://example.com/login?next=/" -> "/login"
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.path or "/"


# ═══════════════════════════════════════════════════════════════
# ELEMENT INFO EXTRACTORS
# ═══════════════════════════════════════════════════════════════

def get_element_name(element: "PageElement") -> str:
    """
    获取元素的显示名称
    
    优先级: name > id > placeholder > text > type
    """
    if element.name:
        return element.name.replace("_", " ").title()
    if element.id:
        return element.id.replace("-", " ").replace("_", " ").title()
    if element.placeholder:
        return element.placeholder
    if element.text:
        return element.text.strip()[:30]
    return f"{element.type.title()} Element"


def get_element_constant_name(element: "PageElement") -> str:
    """
    获取元素的常量名
    
    Examples:
        PageElement(name="username", type="input") -> "USERNAME_INPUT"
        PageElement(text="Submit", type="button") -> "SUBMIT_BUTTON"
    """
    base = element.name or element.id or element.text or "element"
    
    suffix_map = {
        "input": "_INPUT",
        "button": "_BUTTON",
        "link": "_LINK",
        "select": "_SELECT",
    }
    suffix = suffix_map.get(element.type, "")
    
    return to_constant_name(base, suffix)


def get_element_description(element: "PageElement") -> str:
    """
    获取元素描述（用于文档/注释）
    """
    parts = []
    
    if element.type == "input":
        input_type = element.attributes.get("type", "text")
        parts.append(f"{input_type}类型输入框")
        if element.required:
            parts.append("(必填)")
        if element.placeholder:
            parts.append(f"提示: {element.placeholder}")
    elif element.type == "button":
        parts.append("按钮")
        if element.text:
            parts.append(f"文本: {element.text.strip()}")
    elif element.type == "link":
        parts.append("链接")
    elif element.type == "select":
        parts.append("下拉选择框")
    
    return " | ".join(parts) if parts else "-"


def get_element_comment(element: "PageElement") -> str:
    """
    获取元素注释（用于代码注释）
    """
    parts = []
    if element.name:
        parts.append(element.name)
    if element.placeholder:
        parts.append(f"placeholder: {element.placeholder}")
    if element.required:
        parts.append("required")
    return " | ".join(parts) if parts else element.type


# ═══════════════════════════════════════════════════════════════
# PAGE TYPE HELPERS
# ═══════════════════════════════════════════════════════════════

# 页面类型描述映射
PAGE_TYPE_DESCRIPTIONS = {
    "LOGIN": "用户登录页面，提供身份认证功能。",
    "REGISTER": "用户注册页面，用于创建新账号。",
    "FORM": "数据表单页面，用于数据输入和提交。",
    "LIST": "列表页面，展示数据列表，支持分页和筛选。",
    "DETAIL": "详情页面，展示单条数据的详细信息。",
    "DASHBOARD": "仪表盘页面，展示统计数据和概览信息。",
    "SETTINGS": "设置页面，用于配置用户偏好和系统设置。",
}


def get_page_description(page_type: str) -> str:
    """获取页面类型描述"""
    return PAGE_TYPE_DESCRIPTIONS.get(page_type, "页面功能待补充。")


def requires_auth(page_type: str) -> bool:
    """判断页面类型是否需要认证"""
    no_auth_types = {"LOGIN", "REGISTER"}
    return page_type not in no_auth_types

