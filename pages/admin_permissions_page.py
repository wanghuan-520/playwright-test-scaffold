# ═══════════════════════════════════════════════════════════════
# Admin Permissions Page Object
# ═══════════════════════════════════════════════════════════════
"""
Admin Permissions 页面对象
URL: http://localhost:5173/admin/permissions
Type: PROTECTED (需要 admin 账号登录)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminPermissionsPage(BasePage):
    """
    Admin Permissions 页面对象
    
    职责：封装 Permissions 管理页面元素和操作
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 页面标题
    PAGE_TITLE = 'h2:has-text("Permissions")'
    PAGE_SUBTITLE = 'text=Manage permissions for roles, users and clients'
    
    # Tab 选项卡 (使用 ARIA role)
    ROLE_PERMISSIONS_TAB = '[role="tab"]:has-text("Role Permissions")'
    USER_PERMISSIONS_TAB = '[role="tab"]:has-text("User Permissions")'
    
    # 角色选择器
    ROLE_SELECTOR = 'text=Select Role'
    MEMBER_ROLE_BUTTON = 'button:has-text("member")'
    ADMIN_ROLE_BUTTON = 'button:has-text("admin")'
    
    # 权限操作按钮
    GRANT_ALL_BUTTON = 'button:has-text("Grant All")'
    REVOKE_ALL_BUTTON = 'button:has-text("Revoke All")'
    COLLAPSE_ALL_BUTTON = 'button:has-text("Collapse All")'
    SAVE_BUTTON = 'button:has-text("Save")'
    
    # 权限分组（中文名称 - 这是一个 bug）
    IDENTITY_MANAGEMENT_GROUP = 'button:has-text("身份标识管理")'
    SETTINGS_MANAGEMENT_GROUP = 'button:has-text("设置管理")'
    
    # 搜索框
    SEARCH_INPUT = 'input[placeholder*="Search permissions"]'
    
    # 页面 URL
    URL = 'http://localhost:5173/admin/permissions'
    URL_PATH = '/admin/permissions'
    
    # 页面加载标识
    page_loaded_indicator = 'h2:has-text("Permissions")'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到 Permissions 页面"""
        logger.info("导航到 Admin Permissions 页面")
        self.goto(self.URL, wait_for_load=False)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def switch_to_role_permissions(self) -> None:
        """切换到角色权限 Tab"""
        self.page.get_by_role("tab", name="Role Permissions").click()
    
    def switch_to_user_permissions(self) -> None:
        """切换到用户权限 Tab"""
        self.page.get_by_role("tab", name="User Permissions").click()
    
    def select_member_role(self) -> None:
        """选择 member 角色"""
        self.click(self.MEMBER_ROLE_BUTTON)
    
    def select_admin_role(self) -> None:
        """选择 admin 角色"""
        self.click(self.ADMIN_ROLE_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def has_chinese_permission_names(self) -> bool:
        """检查是否存在中文权限名称（i18n bug）"""
        chinese_patterns = ["身份标识管理", "角色管理", "设置管理", "用户管理", "创建", "编辑", "删除"]
        for pattern in chinese_patterns:
            if self.page.locator(f'text={pattern}').count() > 0:
                return True
        return False
    
    def get_permission_group_names(self) -> list:
        """获取所有权限分组名称"""
        groups = self.page.locator('button[class*="cursor-pointer"]').all()
        return [g.text_content() for g in groups if g.text_content()]

