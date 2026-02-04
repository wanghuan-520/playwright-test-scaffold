# ═══════════════════════════════════════════════════════════════
# Admin Roles Page Object
# ═══════════════════════════════════════════════════════════════
"""
Admin Roles 页面对象
URL: http://localhost:5173/admin/roles
Type: PROTECTED (需要 admin 账号登录)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminRolesPage(BasePage):
    """
    Admin Roles 页面对象
    
    职责：封装 Roles 管理页面元素和操作
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 页面标题
    PAGE_TITLE = 'h2:has-text("Roles")'
    PAGE_SUBTITLE = 'text=Manage roles and their permissions'
    
    # 创建角色按钮
    CREATE_ROLE_BUTTON = 'button:has-text("Create Role")'
    
    # 角色卡片
    ROLE_CARD = '.cursor-pointer:has(h3)'  # 角色卡片容器
    ROLE_CARD_NAME = 'h3'  # 角色名称
    ROLE_CARD_USERS_COUNT = 'text=/\\d+ Users/'  # 用户数量
    ROLE_CARD_PERMISSIONS_COUNT = 'text=/\\d+ Permissions/'  # 权限数量
    
    # 特定角色卡片
    MEMBER_ROLE_CARD = 'h3:has-text("member")'
    ADMIN_ROLE_CARD = 'h3:has-text("admin")'
    
    # 角色标签
    DEFAULT_TAG = 'text=Default'
    STATIC_TAG = 'text=Static'
    
    # 页面 URL
    URL = 'http://localhost:5173/admin/roles'
    URL_PATH = '/admin/roles'
    
    # 页面加载标识
    page_loaded_indicator = 'h2:has-text("Roles")'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到 Roles 页面"""
        logger.info("导航到 Admin Roles 页面")
        self.goto(self.URL, wait_for_load=False)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # DATA EXTRACTION
    # ═══════════════════════════════════════════════════════════════
    
    def get_role_count(self) -> int:
        """获取角色数量"""
        cards = self.page.locator(self.ROLE_CARD).all()
        return len(cards)
    
    def get_role_user_count(self, role_name: str) -> str:
        """获取特定角色的用户数量文本"""
        card = self.page.locator(f'text={role_name}').locator('..').locator('..')
        user_count = card.locator(self.ROLE_CARD_USERS_COUNT).text_content()
        return user_count or ""
    
    def get_member_role_user_count(self) -> str:
        """获取 member 角色的用户数量"""
        return self.get_role_user_count("member")
    
    def get_admin_role_user_count(self) -> str:
        """获取 admin 角色的用户数量"""
        return self.get_role_user_count("admin")
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def click_create_role(self) -> None:
        """点击创建角色按钮"""
        logger.info("点击 Create Role 按钮")
        self.click(self.CREATE_ROLE_BUTTON)
    
    def click_role_card(self, role_name: str) -> None:
        """点击特定角色卡片"""
        logger.info(f"点击角色卡片: {role_name}")
        self.page.locator(f'h3:has-text("{role_name}")').click()

