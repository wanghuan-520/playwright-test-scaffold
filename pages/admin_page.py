# ═══════════════════════════════════════════════════════════════
# Admin Page Object (Admin 首页/入口)
# ═══════════════════════════════════════════════════════════════
"""
Admin 管理后台页面对象
URL: http://localhost:5173/admin/users (默认入口)
Type: PROTECTED (需要 admin 账号登录)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminPage(BasePage):
    """
    Admin 管理后台页面对象
    
    职责：封装 Admin 管理后台的公共元素和操作
    注意：admin 账号只能查看，不能做任何改动！
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS (使用 Playwright MCP 定位)
    # ═══════════════════════════════════════════════════════════════
    
    # 侧边栏导航
    SIDEBAR_PROFILE_LINK = 'a[href="/account/profile"]'
    SIDEBAR_PASSWORD_LINK = 'a[href="/account/password"]'
    SIDEBAR_USERS_LINK = 'a[href="/admin/users"]'
    SIDEBAR_ROLES_LINK = 'a[href="/admin/roles"]'
    SIDEBAR_PERMISSIONS_LINK = 'a[href="/admin/permissions"]'
    
    # 返回按钮
    BACK_BUTTON = 'button:has-text("Back")'
    
    # 页面标题
    PAGE_TITLE = 'h1:has-text("Administration")'
    
    # 首页 Logo
    HOME_LINK = 'a[href="/"]'
    
    # 页面 URL
    URL = 'http://localhost:5173/admin/users'
    URL_PATH = '/admin/users'
    
    # 页面加载标识
    page_loaded_indicator = 'h1:has-text("Administration")'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到 Admin 页面"""
        logger.info("导航到 Admin 管理页面")
        self.goto(self.URL, wait_for_load=False)
        try:
            self.page.wait_for_function(
                "() => { const root = document.getElementById('root'); return root && root.children.length > 0; }",
                timeout=30000
            )
        except Exception:
            pass
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            root_has_content = self.page.evaluate("""() => {
                const root = document.getElementById('root');
                return root && root.children.length > 0;
            }""")
            if not root_has_content:
                try:
                    self.page.wait_for_function(
                        "() => { const root = document.getElementById('root'); return root && root.children.length > 0; }",
                        timeout=30000
                    )
                except Exception:
                    pass
            
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # SIDEBAR NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def go_to_users(self) -> None:
        """导航到 Users 页面"""
        logger.info("导航到 Users 页面")
        self.click(self.SIDEBAR_USERS_LINK)
    
    def go_to_roles(self) -> None:
        """导航到 Roles 页面"""
        logger.info("导航到 Roles 页面")
        self.click(self.SIDEBAR_ROLES_LINK)
    
    def go_to_permissions(self) -> None:
        """导航到 Permissions 页面"""
        logger.info("导航到 Permissions 页面")
        self.click(self.SIDEBAR_PERMISSIONS_LINK)
    
    def go_to_profile(self) -> None:
        """导航到 Profile 页面"""
        logger.info("导航到 Profile 页面")
        self.click(self.SIDEBAR_PROFILE_LINK)
    
    def go_to_password(self) -> None:
        """导航到 Password 页面"""
        logger.info("导航到 Password 页面")
        self.click(self.SIDEBAR_PASSWORD_LINK)
    
    def click_back(self) -> None:
        """点击返回按钮"""
        logger.info("点击返回按钮")
        self.click(self.BACK_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def is_on_admin_page(self) -> bool:
        """检查当前是否在 Admin 页面"""
        url = self.page.url or ""
        return "/admin/" in url.lower()
    
    def has_sidebar(self) -> bool:
        """检查侧边栏是否可见"""
        return (
            self.page.locator(self.SIDEBAR_USERS_LINK).is_visible() and
            self.page.locator(self.SIDEBAR_ROLES_LINK).is_visible()
        )

