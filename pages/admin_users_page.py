# ═══════════════════════════════════════════════════════════════
# Admin Users Page Object
# ═══════════════════════════════════════════════════════════════
"""
Admin Users 页面对象
URL: http://localhost:5173/admin/users
Type: PROTECTED (需要 admin 账号登录)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminUsersPage(BasePage):
    """
    Admin Users 页面对象
    
    职责：封装 Users 管理页面元素和操作
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 页面标题
    PAGE_TITLE = 'h2:has-text("Users")'
    PAGE_SUBTITLE = 'text=Manage system users and their permissions'
    
    # 操作按钮
    INVITE_BUTTON = 'button:has-text("Invite")'
    ADD_USER_BUTTON = 'button:has-text("Add User")'
    
    # 统计卡片
    TOTAL_USERS_STAT = 'text=Total Users'
    ACTIVE_NOW_STAT = 'text=Active Now'
    ROLES_STAT = 'text=Roles'
    ADMINS_STAT = 'text=Admins'
    
    # 搜索和过滤
    SEARCH_INPUT = 'searchbox'
    ALL_ROLES_FILTER = 'button:has-text("All Roles")'
    ALL_STATUS_FILTER = 'button:has-text("All Status")'
    
    # 用户表格
    USER_TABLE = 'table'
    USER_TABLE_HEADER = 'columnheader'
    USER_TABLE_ROW = 'row'
    
    # Add User 对话框 (使用 ARIA role)
    ADD_USER_DIALOG = '[role="dialog"]'
    DIALOG_TITLE = '[role="dialog"] h2:has-text("Create New User")'
    FIRST_NAME_INPUT = '[role="dialog"] input[placeholder="John"]'
    LAST_NAME_INPUT = '[role="dialog"] input[placeholder="Doe"]'
    EMAIL_INPUT = '[role="dialog"] input[placeholder="john@example.com"]'
    USERNAME_INPUT = '[role="dialog"] input[placeholder="johndoe"]'
    PASSWORD_INPUT = '[role="dialog"] input[placeholder="Enter password"]'
    PHONE_INPUT = '[role="dialog"] input[placeholder*="+1"]'
    MEMBER_ROLE_BUTTON = '[role="dialog"] button:has-text("member")'
    ADMIN_ROLE_BUTTON = '[role="dialog"] button:has-text("admin")'
    ACTIVE_SWITCH = '[role="dialog"] [role="switch"]'
    CANCEL_BUTTON = '[role="dialog"] button:has-text("Cancel")'
    CREATE_USER_BUTTON = '[role="dialog"] button:has-text("Create User")'
    
    # 页面 URL
    URL = 'http://localhost:5173/admin/users'
    URL_PATH = '/admin/users'
    
    # 页面加载标识
    page_loaded_indicator = 'h2:has-text("Users")'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到 Users 页面"""
        logger.info("导航到 Admin Users 页面")
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
    
    def get_total_users_count(self) -> str:
        """获取 Total Users 统计值"""
        stat_card = self.page.locator(self.TOTAL_USERS_STAT).locator('..')
        # 查找下一个兄弟元素或子元素中的数字
        text = stat_card.text_content() or ""
        import re
        match = re.search(r'(\d+)', text)
        return match.group(1) if match else "0"
    
    def get_admins_count(self) -> str:
        """获取 Admins 统计值"""
        stat_card = self.page.locator(self.ADMINS_STAT).locator('..')
        text = stat_card.text_content() or ""
        import re
        match = re.search(r'(\d+)', text)
        return match.group(1) if match else "0"
    
    def get_user_rows(self) -> list:
        """获取用户表格行"""
        return self.page.locator('tbody tr, rowgroup row').all()
    
    def wait_for_data_loaded(self, timeout: int = 5000) -> bool:
        """等待数据加载完成（Total Users 不为 0）"""
        try:
            self.page.wait_for_function(
                """() => {
                    const text = document.body.innerText;
                    const match = text.match(/Total Users\\s*(\\d+)/);
                    return match && parseInt(match[1]) > 0;
                }""",
                timeout=timeout
            )
            return True
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def click_add_user(self) -> None:
        """点击 Add User 按钮"""
        logger.info("点击 Add User 按钮")
        self.page.get_by_role("button", name="Add User").click()
    
    def click_invite(self) -> None:
        """点击 Invite 按钮"""
        logger.info("点击 Invite 按钮")
        self.page.get_by_role("button", name="Invite").click()
    
    def close_dialog(self) -> None:
        """关闭对话框"""
        self.page.get_by_role("button", name="Cancel").click()
    
    def search_user(self, query: str) -> None:
        """搜索用户"""
        logger.info(f"搜索用户: {query}")
        self.page.get_by_role("searchbox").fill(query)
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def is_add_user_dialog_visible(self) -> bool:
        """检查 Add User 对话框是否可见"""
        return self.page.locator(self.ADD_USER_DIALOG).is_visible() and \
               self.page.locator(self.DIALOG_TITLE).is_visible()
    
    def has_console_html_nesting_errors(self) -> bool:
        """
        检查是否有 HTML 嵌套错误
        需要在浏览器控制台中检查
        """
        # 这个需要通过 page.on('console') 来捕获
        # 这里仅作为标记
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # DIALOG OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def fill_create_user_form(
        self,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        username: str = "",
        password: str = "",
        phone: str = "",
        role: str = "member",
        active: bool = True
    ) -> None:
        """
        填写创建用户表单
        
        Args:
            first_name: 名字
            last_name: 姓氏
            email: 邮箱（必填）
            username: 用户名（必填）
            password: 密码（必填）
            phone: 电话
            role: 角色（member/admin）
            active: 是否激活
        """
        logger.info(f"填写创建用户表单: {username}, {email}")
        
        if first_name:
            self.page.locator(self.FIRST_NAME_INPUT).fill(first_name)
        if last_name:
            self.page.locator(self.LAST_NAME_INPUT).fill(last_name)
        if email:
            self.page.locator(self.EMAIL_INPUT).fill(email)
        if username:
            self.page.locator(self.USERNAME_INPUT).fill(username)
        if password:
            self.page.locator(self.PASSWORD_INPUT).fill(password)
        if phone:
            self.page.locator(self.PHONE_INPUT).fill(phone)
        
        # 角色选择
        if role == "admin":
            self.page.locator(self.ADMIN_ROLE_BUTTON).click()
        else:
            self.page.locator(self.MEMBER_ROLE_BUTTON).click()
        
        # Active 开关
        switch = self.page.locator(self.ACTIVE_SWITCH)
        is_checked = switch.is_checked()
        if active != is_checked:
            switch.click()
    
    def click_create_user(self) -> None:
        """点击 Create User 按钮"""
        logger.info("点击 Create User 按钮")
        self.page.locator(self.CREATE_USER_BUTTON).click()
    
    def filter_by_role(self, role: str) -> None:
        """
        按角色筛选
        
        Args:
            role: 角色名称 (All Roles/member/admin)
        """
        logger.info(f"按角色筛选: {role}")
        self.page.locator(self.ALL_ROLES_FILTER).click()
        self.page.wait_for_timeout(500)
        # 使用 menuitem 选择器（Radix UI 下拉菜单）
        self.page.get_by_role("menuitem", name=role).click()
    
    def filter_by_status(self, status: str) -> None:
        """
        按状态筛选
        
        Args:
            status: 状态 (All Status/Active/Inactive)
        """
        logger.info(f"按状态筛选: {status}")
        self.page.locator(self.ALL_STATUS_FILTER).click()
        self.page.wait_for_timeout(500)
        # 使用 menuitem 选择器（Radix UI 下拉菜单）
        self.page.get_by_role("menuitem", name=status).click()
    
    def get_visible_user_count(self) -> int:
        """获取当前可见的用户行数"""
        rows = self.page.locator('table tbody tr, table rowgroup:nth-child(2) row')
        return rows.count()
    
    def get_user_by_username(self, username: str):
        """根据用户名获取用户行"""
        return self.page.locator(f'row:has-text("{username}"), tr:has-text("{username}")')
    
    def click_user_action(self, username: str) -> None:
        """点击用户行的 Actions 按钮"""
        row = self.get_user_by_username(username)
        row.locator('button').last.click()
    
    def wait_for_search_results(self, timeout: int = 3000) -> None:
        """等待搜索结果加载"""
        self.page.wait_for_timeout(timeout)
    
    # ═══════════════════════════════════════════════════════════════
    # PAGINATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_showing_text(self) -> str:
        """获取 'Showing X to Y of Z results' 文本"""
        try:
            text = self.page.locator('text=/Showing \\d+ to \\d+ of \\d+ results/').text_content()
            return text or ""
        except Exception:
            return ""
    
    def click_page_number(self, page_num: int) -> None:
        """点击指定页码"""
        logger.info(f"点击页码: {page_num}")
        self.page.get_by_role("button", name=str(page_num), exact=True).click()
    
    def click_next_page(self) -> None:
        """点击下一页按钮"""
        logger.info("点击下一页")
        # 下一页按钮是最后一个 button（带箭头图标）
        self.page.locator('button:has(img)').last.click()
    
    def click_prev_page(self) -> None:
        """点击上一页按钮"""
        logger.info("点击上一页")
        # 上一页按钮是第一个 button（带箭头图标）
        self.page.locator('button:has(img)[disabled]').first.click()
    
    def change_per_page(self, per_page: int) -> None:
        """
        切换每页显示数量
        
        Args:
            per_page: 每页数量 (10/20/50/100)
        """
        logger.info(f"切换每页显示: {per_page}")
        self.page.locator('select, combobox').select_option(str(per_page))
    
    def get_current_page(self) -> int:
        """获取当前页码"""
        try:
            # 查找 active 状态的页码按钮
            active_btn = self.page.locator('button[active], button.active')
            if active_btn.count() > 0:
                return int(active_btn.text_content() or "1")
        except Exception:
            pass
        return 1
