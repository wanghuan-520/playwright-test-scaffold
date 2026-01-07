# ═══════════════════════════════════════════════════════════════
# Admin Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
Admin 页面对象
URL: https://localhost:3000/admin
Type: FORM
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminPage(BasePage):
    """
    Admin 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # toggle_user_menu | placeholder: toggle_user_menu
    TOGGLE_USER_MENU_BUTTON = 'role=button[name="Toggle user menu"]'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # home | placeholder: home
    HOME_LINK = 'role=link[name="Home"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    
    URL = 'https://localhost:3000/admin'
    page_loaded_indicator = 'role=button[name="Toggle user menu"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 Admin 页面")
        self.goto(self.URL)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=5000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def click_toggle_user_menu(self) -> None:
        """点击 toggle_user_menu 按钮"""
        logger.info("点击 toggle_user_menu 按钮")
        self.click(self.TOGGLE_USER_MENU_BUTTON)

    def click_open_next_js_dev_tools(self) -> None:
        """点击 open_next_js_dev_tools 按钮"""
        logger.info("点击 open_next_js_dev_tools 按钮")
        self.click(self.OPEN_NEXT_JS_DEV_TOOLS_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
