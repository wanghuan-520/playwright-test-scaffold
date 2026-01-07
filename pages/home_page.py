# ═══════════════════════════════════════════════════════════════
# Home Page Object
# Generated: 2025-12-25 09:21:32
# ═══════════════════════════════════════════════════════════════
"""
Home 页面对象
URL: https://localhost:3000/
Type: LOGIN
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class HomePage(BasePage):
    """
    Home 页面对象
    
    职责：封装页面元素选择器，提供页面操作方法
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # sign_in | placeholder: sign_in
    SIGN_IN_BUTTON = 'role=button[name="Sign In"]'

    # get_started | placeholder: get_started
    GET_STARTED_BUTTON = 'role=button[name="Get Started"]'

    # create_workflow | placeholder: create_workflow
    CREATE_WORKFLOW_BUTTON = 'role=button[name="Create Workflow"]'

    # view_on_github | placeholder: view_on_github
    VIEW_ON_GITHUB_BUTTON = 'role=button[name="View on GitHub"]'

    # dashboard | placeholder: dashboard
    DASHBOARD_BUTTON = 'role=button[name="Dashboard"]'

    # open_next_js_dev_tools | placeholder: open_next_js_dev_tools
    OPEN_NEXT_JS_DEV_TOOLS_BUTTON = 'role=button[name="Open Next.js Dev Tools"]'

    # aevatar_ai | placeholder: aevatar_ai
    AEVATAR_AI_LINK = 'role=link[name="Aevatar AI"]'

    # workflow | placeholder: workflow
    WORKFLOW_LINK = 'role=link[name="Workflow"]'

    # github | placeholder: github
    GITHUB_LINK = 'role=link[name="GitHub"]'

    # get_started | placeholder: get_started
    GET_STARTED_LINK = 'role=link[name="Get Started"]'

    # create_workflow | placeholder: create_workflow
    CREATE_WORKFLOW_LINK = 'role=link[name="Create Workflow"]'

    # view_on_github | placeholder: view_on_github
    VIEW_ON_GITHUB_LINK = 'role=link[name="View on GitHub"]'

    # dashboard | placeholder: dashboard
    DASHBOARD_LINK = 'role=link[name="Dashboard"]'

    # terms_of_service | placeholder: terms_of_service
    TERMS_OF_SERVICE_LINK = 'role=link[name="Terms of Service"]'

    # privacy | placeholder: privacy
    PRIVACY_LINK = 'role=link[name="Privacy"]'

    
    URL = 'https://localhost:3000/'
    page_loaded_indicator = 'role=button[name="Sign In"]'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到页面"""
        logger.info(f"导航到 Home 页面")
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

    def click_create_workflow(self) -> None:
        """点击 create_workflow 按钮"""
        logger.info("点击 create_workflow 按钮")
        self.click(self.CREATE_WORKFLOW_BUTTON)

    def click_view_on_github(self) -> None:
        """点击 view_on_github 按钮"""
        logger.info("点击 view_on_github 按钮")
        self.click(self.VIEW_ON_GITHUB_BUTTON)

    def click_dashboard(self) -> None:
        """点击 dashboard 按钮"""
        logger.info("点击 dashboard 按钮")
        self.click(self.DASHBOARD_BUTTON)

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
