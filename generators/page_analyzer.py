# ═══════════════════════════════════════════════════════════════════
import re
# Playwright Test Scaffold - Page Analyzer (Coordinator)
# ═══════════════════════════════════════════════════════════════════
"""
页面分析器 - 协调器
统一协调元素提取器和页面类型检测
"""

from playwright.sync_api import sync_playwright, Page
from typing import Dict, Optional
from generators.page_types import PageElement, PageInfo
from generators.element_extractor import ElementExtractor
from utils.logger import get_logger
from utils.config import ConfigManager
import json

logger = get_logger(__name__)


class PageAnalyzer:
    """页面分析器 - 协调器"""
    
    def __init__(self):
        """初始化元素提取器"""
        self.extractor = ElementExtractor()
        self.config = ConfigManager()
    
class PageAnalyzer:
    """
    页面分析器
    
    自动分析页面结构，识别：
    - 输入框（text, email, password, number等）
    - 按钮（submit, button, link-button）
    - 链接（导航、操作）
    - 表单结构
    - 页面类型
    
    使用方式:
        analyzer = PageAnalyzer()
        page_info = analyzer.analyze("https://example.com/login")
        print(page_info.page_type)  # LOGIN
        print(page_info.elements)   # [PageElement(...), ...]
    """
    
    # 页面类型识别规则
    PAGE_TYPE_RULES = {
        "LOGIN": {
            "url_patterns": [r"/login", r"/signin", r"/auth"],
            "element_patterns": ["input[type='password']", "button:has-text('Login')", "button:has-text('Sign in')"],
        },
        "REGISTER": {
            "url_patterns": [r"/register", r"/signup", r"/join"],
            "element_patterns": ["input[type='password']", "button:has-text('Register')", "button:has-text('Sign up')"],
        },
        "FORM": {
            "url_patterns": [r"/edit", r"/create", r"/new", r"/add"],
            "element_patterns": ["form", "input", "textarea", "select"],
        },
        "LIST": {
            "url_patterns": [r"/list", r"/index", r"/all"],
            "element_patterns": ["table", "[role='grid']", ".pagination", ".list-item"],
        },
        "DETAIL": {
            "url_patterns": [r"/view", r"/detail", r"/show", r"/\d+$"],
            "element_patterns": [".detail", ".view", "button:has-text('Edit')"],
        },
        "DASHBOARD": {
            "url_patterns": [r"/dashboard", r"/home", r"/overview"],
            "element_patterns": [".card", ".widget", ".chart", ".stats"],
        },
        "SETTINGS": {
            "url_patterns": [r"/settings", r"/profile", r"/preferences", r"/config"],
            "element_patterns": ["input", "select", "button:has-text('Save')"],
        },
    }
    
    def __init__(self):
        """初始化分析器"""
        self.config = ConfigManager()
    
    def analyze(self, url: str, auth_callback: callable = None) -> PageInfo:
        """
        分析页面
        
        Args:
            url: 页面URL
            auth_callback: 认证回调函数（如果页面需要登录）
            
        Returns:
            PageInfo: 页面信息
        """
        logger.info(f"开始分析页面: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True
            )
            page = context.new_page()
            
            try:
                # 如果需要认证
                if auth_callback:
                    auth_callback(page)
                
                # 导航到页面
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                # 分析页面
                page_info = self._analyze_page(page, url)
                
                logger.info(f"页面分析完成: {page_info.page_type}")
                return page_info
                
            finally:
                browser.close()
    
    def _analyze_page(self, page: Page, url: str) -> PageInfo:
        """
        分析页面内容
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            PageInfo: 页面信息
        """
        title = page.title()
        
        # 识别页面类型
        page_type = self._detect_page_type(page, url)
        
        # 获取元素
        elements = self.extractor._get_elements(page)
        
        # 获取表单信息
        forms = self._get_forms(page)
        
        # 获取导航信息
        navigation = self._get_navigation(page)
        
        return PageInfo(
            url=url,
            title=title,
            page_type=page_type,
            elements=elements,
            forms=forms,
            navigation=navigation
        )
    
    def _detect_page_type(self, page: Page, url: str) -> str:
        """
        识别页面类型
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            str: 页面类型
        """
        scores = {page_type: 0 for page_type in self.PAGE_TYPE_RULES}
        
        for page_type, rules in self.PAGE_TYPE_RULES.items():
            # URL匹配
            for pattern in rules["url_patterns"]:
                if re.search(pattern, url, re.IGNORECASE):
                    scores[page_type] += 2
            
            # 元素匹配
            for selector in rules["element_patterns"]:
                try:
                    if page.locator(selector).count() > 0:
                        scores[page_type] += 1
                except:
                    pass
        
        # 返回得分最高的类型
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else "FORM"
    

    def to_dict(self, page_info: PageInfo) -> Dict:
        """转换为字典"""
        return {
            "url": page_info.url,
            "title": page_info.title,
            "page_type": page_info.page_type,
            "elements": [asdict(e) for e in page_info.elements],
            "forms": page_info.forms,
            "navigation": page_info.navigation,
        }
    
    def to_json(self, page_info: PageInfo, file_path: str = None) -> str:
        """
        转换为JSON
        
        Args:
            page_info: 页面信息
            file_path: 保存路径（可选）
            
        Returns:
            str: JSON字符串
        """
        data = self.to_dict(page_info)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"页面分析结果已保存: {file_path}")
        
        return json_str

