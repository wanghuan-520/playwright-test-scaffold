# ═══════════════════════════════════════════════════════════════
# Workflow Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
Workflow 页面对象
URL: https://localhost:3000/workflow
Type: LOGIN
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowPage(BasePage):
    """
    Workflow 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # sign_in | placeholder: sign_in
    SIGN_IN_BUTTON = 'role=button[name="Sign In"]'

    # get_started | placeholder: get_started
    GET_STARTED_BUTTON = 'role=button[name="Get Started"]'

    # choose_file | placeholder: choose_file
    CHOOSE_FILE_BUTTON = 'role=button[name="Choose File"]'

    # import_workflow | placeholder: import_workflow
    IMPORT_WORKFLOW_BUTTON = 'role=button[name="Import Workflow"]'

    # new_workflow | placeholder: new_workflow
    NEW_WORKFLOW_BUTTON = 'role=button[name="New Workflow"]'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # open_issues_overlay | placeholder: open_issues_overlay
    OPEN_ISSUES_OVERLAY_BUTTON = 'role=button[name="Open issues overlay"]'

    # collapse_issues_badge | placeholder: collapse_issues_badge
    COLLAPSE_ISSUES_BADGE_BUTTON = 'role=button[name="Collapse issues badge"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    # github | placeholder: github
    GITHUB_LINK = 'role=link[name="GitHub"]'

    # get_started | placeholder: get_started
    GET_STARTED_LINK = 'role=link[name="Get Started"]'

    
    URL = 'https://localhost:3000/workflow'
    page_loaded_indicator = 'role=button[name="Sign In"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 Workflow 页面")
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

    def click_sign_in(self) -> None:
        """点击 sign_in 按钮"""
        logger.info("点击 sign_in 按钮")
        self.click(self.SIGN_IN_BUTTON)

    def click_get_started(self) -> None:
        """点击 get_started 按钮"""
        logger.info("点击 get_started 按钮")
        self.click(self.GET_STARTED_BUTTON)

    def click_choose_file(self) -> None:
        """点击 choose_file 按钮"""
        logger.info("点击 choose_file 按钮")
        self.click(self.CHOOSE_FILE_BUTTON)

    def click_import_workflow(self) -> None:
        """点击 import_workflow 按钮"""
        logger.info("点击 import_workflow 按钮")
        self.click(self.IMPORT_WORKFLOW_BUTTON)

    def click_new_workflow(self) -> None:
        """点击 new_workflow 按钮"""
        logger.info("点击 new_workflow 按钮")
        self.click(self.NEW_WORKFLOW_BUTTON)

    def click_open_next_js_dev_tools(self) -> None:
        """点击 open_next_js_dev_tools 按钮"""
        logger.info("点击 open_next_js_dev_tools 按钮")
        self.click(self.OPEN_NEXT_JS_DEV_TOOLS_BUTTON)

    def click_open_issues_overlay(self) -> None:
        """点击 open_issues_overlay 按钮"""
        logger.info("点击 open_issues_overlay 按钮")
        self.click(self.OPEN_ISSUES_OVERLAY_BUTTON)

    def click_collapse_issues_badge(self) -> None:
        """点击 collapse_issues_badge 按钮"""
        logger.info("点击 collapse_issues_badge 按钮")
        self.click(self.COLLAPSE_ISSUES_BADGE_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_validation_errors(self) -> list:
        """获取页面上的验证错误信息"""
        return self.utils.get_validation_errors()
    
    def has_validation_error(self) -> bool:
        """检查是否有验证错误"""
        return self.utils.has_validation_error()
