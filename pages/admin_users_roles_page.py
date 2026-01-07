# ═══════════════════════════════════════════════════════════════
# AdminUsersRoles Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
AdminUsersRoles 页面对象
URL: https://localhost:3000/admin/users/roles
Type: FORM
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminUsersRolesPage(BasePage):
    """
    AdminUsersRoles 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # search | placeholder: search
    SEARCH_INPUT = 'role=textbox[name="Search..."]'

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

    
    URL = 'https://localhost:3000/admin/users/roles'
    page_loaded_indicator = 'role=textbox[name="Search..."]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 AdminUsersRoles 页面")
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

    def fill_search(self, value: str) -> None:
        """填写 search"""
        logger.info("填写 search (len={len(value)})")
        self.fill(self.SEARCH_INPUT, value)
    
    def get_search_value(self) -> str:
        """获取 search 的值"""
        # NOTE: 用 super() 避免方法名与 BasePage.get_input_value 冲突导致递归
        return super().get_input_value(self.SEARCH_INPUT)

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
