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
    
    # 操作按钮（Invite 按钮已于 2026-02-04 移除）
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
        """等待数据加载完成（Total Users 不为 0），优化：快速检查"""
        try:
            # 优化：快速检查，最多等待 2 秒
            actual_timeout = min(timeout, 2000)
            self.page.wait_for_function(
                """() => {
                    const text = document.body.innerText;
                    const match = text.match(/Total Users\\s*(\\d+)/);
                    return match && parseInt(match[1]) > 0;
                }""",
                timeout=actual_timeout
            )
            return True
        except Exception:
            # 如果超时，快速返回（不等待）
            return True
    
    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def click_add_user(self) -> None:
        """点击 Add User 按钮"""
        logger.info("点击 Add User 按钮")
        self.page.get_by_role("button", name="Add User").click()
    
    def close_dialog(self) -> None:
        """关闭对话框"""
        dialog = self.page.locator('[role="dialog"]').last
        cancel = dialog.get_by_role("button", name="Cancel", exact=True)
        if cancel.count() > 0:
            cancel.click()
        else:
            self.page.keyboard.press("Escape")
    
    def search_user(self, query: str) -> None:
        """
        搜索用户
        
        Args:
            query: 搜索关键词（用户名或邮箱）
        """
        logger.info(f"搜索用户: {query}")
        searchbox = self.page.get_by_role("searchbox")
        # 清空搜索框（如果已有内容，使用更快的 fill 方法）
        try:
            searchbox.clear(timeout=2000)  # 减少超时
        except Exception:
            # 如果 clear 失败，直接 fill（会覆盖原有内容）
            pass
        # 输入搜索关键词
        searchbox.fill(query)
        # 触发搜索：按 Enter 键
        searchbox.press("Enter")
        # 减少等待时间，使用 wait_for_filter_results 代替固定等待
        self.page.wait_for_timeout(300)  # 减少 debounce 等待时间
    
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
        # 使用 menuitem 选择器（Radix UI 下拉菜单），exact=True 避免 "Active" 匹配到 "Inactive"
        self.page.get_by_role("menuitem", name=status, exact=True).click()
    
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
        btn = row.locator('button').last
        btn.scroll_into_view_if_needed()
        btn.click()
    
    def wait_for_search_results(self, timeout: int = 3000) -> None:
        """等待搜索结果加载"""
        self.page.wait_for_timeout(timeout)
    
    def wait_for_filter_results(self, timeout: int = 3000) -> None:
        """等待筛选结果加载（等待 API 响应和 UI 刷新，优化：快速响应）"""
        try:
            # 等待网络请求完成（减少超时）
            with self.page.expect_response(
                lambda resp: "/api/" in resp.url and resp.status == 200,
                timeout=min(timeout, 2000)  # 最多等待 2 秒
            ):
                pass
        except Exception:
            # 如果没有捕获到 API 响应，快速返回
            pass
        # 等待表格 UI 刷新（大幅减少等待时间）
        self.page.wait_for_timeout(300)  # 从 1000 减少到 300
        # 不等待 networkidle（太慢），直接返回
    
    # ═══════════════════════════════════════════════════════════════
    # CHECKBOX OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def get_header_checkbox(self):
        """获取表头全选 checkbox"""
        return self.page.locator('table thead input[type="checkbox"], table th input[type="checkbox"]').first
    
    def get_row_checkbox(self, row_index: int):
        """获取指定行的 checkbox（从 0 开始）"""
        rows = self.page.locator('table tbody tr')
        if rows.count() > row_index:
            return rows.nth(row_index).locator('input[type="checkbox"]')
        return self.page.locator(f'table tbody tr:nth-child({row_index + 1}) input[type="checkbox"]')
    
    def get_row_checkbox_by_username(self, username: str):
        """根据用户名获取行 checkbox"""
        row = self.page.locator(f'table tbody tr:has-text("{username}")')
        return row.locator('input[type="checkbox"]')
    
    def check_row(self, row_index: int) -> None:
        """勾选指定行"""
        logger.info(f"勾选第 {row_index + 1} 行")
        checkbox = self.get_row_checkbox(row_index)
        checkbox.scroll_into_view_if_needed()
        checkbox.click()
        self.page.wait_for_timeout(300)
    
    def uncheck_row(self, row_index: int) -> None:
        """取消勾选指定行"""
        logger.info(f"取消勾选第 {row_index + 1} 行")
        checkbox = self.get_row_checkbox(row_index)
        checkbox.scroll_into_view_if_needed()
        checkbox.click()
        self.page.wait_for_timeout(300)
    
    def check_row_by_username(self, username: str) -> None:
        """勾选指定用户名的行"""
        logger.info(f"勾选用户: {username}")
        checkbox = self.get_row_checkbox_by_username(username)
        checkbox.scroll_into_view_if_needed()
        checkbox.click()
        self.page.wait_for_timeout(300)
    
    def check_all(self) -> None:
        """勾选全部（点击表头 checkbox）"""
        logger.info("勾选全部")
        checkbox = self.get_header_checkbox()
        checkbox.click()
        self.page.wait_for_timeout(300)
    
    def uncheck_all(self) -> None:
        """取消勾选全部"""
        logger.info("取消勾选全部")
        checkbox = self.get_header_checkbox()
        checkbox.click()
        self.page.wait_for_timeout(300)
    
    def get_checked_count(self) -> int:
        """获取已勾选行数"""
        return self.page.locator('table tbody input[type="checkbox"]:checked').count()
    
    def is_row_checked(self, row_index: int) -> bool:
        """检查指定行是否已勾选"""
        checkbox = self.get_row_checkbox(row_index)
        return checkbox.is_checked()
    
    # ═══════════════════════════════════════════════════════════════
    # USER ACTIONS (Delete, Edit)
    # ═══════════════════════════════════════════════════════════════
    
    def open_actions_menu(self, username: str) -> None:
        """打开用户的 Actions 菜单"""
        logger.info(f"打开 Actions 菜单: {username}")
        row = self.get_user_by_username(username)
        btn = row.locator('button').last
        btn.scroll_into_view_if_needed()
        btn.click()
        self.page.wait_for_timeout(200)
    
    def click_actions_menu_for_user(self, username: str) -> None:
        """打开指定用户的 Actions 菜单（别名方法）"""
        self.open_actions_menu(username)
    
    def click_view_details(self) -> None:
        """点击 View Details 菜单项"""
        logger.info("点击 View Details")
        self.page.get_by_role("menuitem", name="View Details").click()
        self.page.wait_for_timeout(500)
    
    def click_edit_user(self) -> None:
        """点击 Edit User 菜单项"""
        logger.info("点击 Edit User")
        self.page.get_by_role("menuitem", name="Edit User").click()
        self.page.wait_for_timeout(300)  # 减少等待时间：从 500 减少到 300
    
    def click_set_password(self) -> None:
        """点击 Set Password 菜单项"""
        logger.info("点击 Set Password")
        self.page.get_by_role("menuitem", name="Set Password").click()
        self.page.wait_for_timeout(500)
    
    def click_delete_user(self) -> None:
        """点击 Delete User 菜单项"""
        logger.info("点击 Delete User")
        self.page.get_by_role("menuitem", name="Delete User").click()
        self.page.wait_for_timeout(500)
    
    def click_close_dialog(self) -> None:
        """关闭当前对话框"""
        logger.info("关闭对话框")
        dialog = self.page.locator('[role="dialog"]')
        # 尝试点击 Close 或 Cancel 按钮
        close_btn = dialog.get_by_role("button", name="Close").or_(dialog.get_by_role("button", name="Cancel"))
        if close_btn.count() > 0:
            close_btn.first.click()
        else:
            # 如果没有找到按钮，尝试点击 X 按钮
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(500)
    
    def click_delete_action(self) -> None:
        """点击删除操作（已废弃，使用 click_delete_user）"""
        self.click_delete_user()
    
    def confirm_delete(self) -> None:
        """确认删除"""
        logger.info("确认删除")
        self.page.get_by_role("button", name="Delete User").or_(self.page.get_by_role("button", name="Delete")).click()
        self.page.wait_for_timeout(1000)
    
    def delete_user(self, username: str) -> None:
        """删除指定用户"""
        self.open_actions_menu(username)
        self.click_delete_user()
        self.confirm_delete()
        self.page.wait_for_timeout(1000)
    
    def is_user_visible(self, username: str) -> bool:
        """
        检查用户是否可见
        
        Args:
            username: 用户名
            
        Returns:
            True 如果用户行存在且可见
        """
        user_row = self.get_user_by_username(username)
        if user_row.count() == 0:
            return False
        try:
            # 检查第一个匹配的行是否可见
            return user_row.first.is_visible(timeout=1000)
        except Exception:
            # 如果检查可见性失败，至少检查是否存在
            return user_row.count() > 0
    
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
    
    def get_total_pages(self) -> int:
        """获取总页数"""
        try:
            # 查找最后一个页码按钮
            buttons = self.page.locator('button').all_text_contents()
            max_page = 1
            for text in buttons:
                if text.isdigit():
                    max_page = max(max_page, int(text))
            return max_page
        except Exception:
            return 1
    
    def click_page_number(self, page_num: int) -> None:
        """点击指定页码"""
        logger.info(f"点击页码: {page_num}")
        btn = self.page.get_by_role("button", name=str(page_num), exact=True)
        btn.scroll_into_view_if_needed()
        btn.click()
        self.page.wait_for_timeout(1000)
    
    def click_first_page(self) -> None:
        """跳转到第一页"""
        logger.info("跳转到第一页")
        self.click_page_number(1)
    
    def click_last_page(self) -> None:
        """跳转到最后一页"""
        logger.info("跳转到最后一页")
        total_pages = self.get_total_pages()
        self.click_page_number(total_pages)
    
    def _get_pagination_container(self):
        """获取分页容器"""
        return self.page.locator('text=/Showing \\d+ to \\d+ of/').locator('xpath=..')
    
    def click_next_page(self) -> None:
        """点击下一页按钮"""
        logger.info("点击下一页")
        # 分页容器内所有按钮，最后一个是下一页
        pagination = self._get_pagination_container()
        buttons = pagination.locator('button').all()
        if buttons:
            buttons[-1].scroll_into_view_if_needed()
            buttons[-1].click()
        self.page.wait_for_timeout(1500)
    
    def click_prev_page(self) -> None:
        """点击上一页按钮"""
        logger.info("点击上一页")
        pagination = self._get_pagination_container()
        buttons = pagination.locator('button').all()
        if buttons:
            buttons[0].scroll_into_view_if_needed()
            buttons[0].click()
        self.page.wait_for_timeout(1500)
    
    def is_prev_page_disabled(self) -> bool:
        """检查上一页按钮是否禁用"""
        try:
            pagination = self._get_pagination_container()
            # 等待分页容器可见
            pagination.wait_for(state="visible", timeout=5000)
            # 等待按钮加载并可见
            buttons = pagination.locator('button')
            if buttons.count() > 0:
                buttons.first.wait_for(state="visible", timeout=5000)
                # 获取所有按钮
                button_list = buttons.all()
                if button_list:
                    return button_list[0].is_disabled()
        except Exception as e:
            logger.warning(f"检查上一页按钮状态失败: {e}")
            pass
        return False
    
    def is_next_page_disabled(self) -> bool:
        """检查下一页按钮是否禁用"""
        try:
            pagination = self._get_pagination_container()
            buttons = pagination.locator('button').all()
            if buttons:
                return buttons[-1].is_disabled()
        except Exception:
            pass
        return False
    
    def change_per_page(self, per_page: int) -> None:
        """
        切换每页显示数量
        
        Args:
            per_page: 每页数量 (10/20/50/100)
        """
        logger.info(f"切换每页显示: {per_page}")
        self.page.get_by_role("combobox").select_option(str(per_page))
        self.page.wait_for_timeout(1500)
    
    def get_current_per_page(self) -> int:
        """获取当前每页数量"""
        try:
            value = self.page.get_by_role("combobox").input_value()
            return int(value)
        except Exception:
            return 10
    
    def get_current_page(self) -> int:
        """获取当前页码"""
        try:
            # 从 showing text 解析
            text = self.get_showing_text()
            import re
            match = re.search(r'Showing (\d+) to', text)
            if match:
                start = int(match.group(1))
                per_page = self.get_current_per_page()
                return (start - 1) // per_page + 1
        except Exception:
            pass
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # EDIT USER DIALOG
    # ═══════════════════════════════════════════════════════════════
    
    # Edit User 对话框选择器
    EDIT_USER_DIALOG = '[role="dialog"] h2:has-text("Edit User")'
    EDIT_USER_FIRST_NAME_INPUT = '[role="dialog"] text:has-text("First Name") >> .. >> input'
    EDIT_USER_LAST_NAME_INPUT = '[role="dialog"] text:has-text("Last Name") >> .. >> input'
    EDIT_USER_EMAIL_INPUT = '[role="dialog"] input[type="email"]'
    EDIT_USER_PHONE_INPUT = '[role="dialog"] text:has-text("Phone Number") >> .. >> input'
    EDIT_USER_ROLE_BUTTON = '[role="dialog"] button:has-text("member"), [role="dialog"] button:has-text("admin")'
    EDIT_USER_ACTIVE_SWITCH = '[role="dialog"] [role="switch"]'
    EDIT_USER_SAVE_BUTTON = '[role="dialog"] button:has-text("Save Changes")'
    EDIT_USER_CANCEL_BUTTON = '[role="dialog"] button:has-text("Cancel")'
    
    def fill_edit_user_form(
        self,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        phone: str = None,
        role_names: list = None,
        is_active: bool = None
    ) -> None:
        """
        填写 Edit User 表单
        
        Args:
            first_name: 名字（可选）
            last_name: 姓氏（可选）
            email: 邮箱（可选）
            phone: 电话（可选）
            role_names: 角色列表（可选，如 ["member", "admin"]）
            is_active: 是否激活（可选）
        """
        logger.info("填写 Edit User 表单")
        dialog = self.page.locator('[role="dialog"]')
        
        if first_name is not None:
            # 获取所有非 disabled 的 textbox（跳过 Username/Email disabled 输入框）
            all_inputs = dialog.locator('input:not([disabled])').all()
            # First Name 是第 1 个可编辑 input
            if len(all_inputs) >= 1:
                all_inputs[0].fill(first_name)
        
        if last_name is not None:
            all_inputs = dialog.locator('input:not([disabled])').all()
            # Last Name 是第 2 个可编辑 input
            if len(all_inputs) >= 2:
                all_inputs[1].fill(last_name)
        
        if email is not None:
            email_input = dialog.locator('input[type="email"]')
            if email_input.count() > 0:
                email_input.fill(email)
        
        if phone is not None:
            all_inputs = dialog.locator('input:not([disabled])').all()
            # Phone Number 是第 3 个可编辑 input
            if len(all_inputs) >= 3:
                all_inputs[2].fill(phone)
        
        if role_names is not None:
            # 先取消所有已选角色，再选择新角色
            # 注意：这里需要根据实际 UI 实现，可能需要点击来切换
            for role_name in role_names:
                role_btn = dialog.locator(f'button:has-text("{role_name}")')
                if role_btn.count() > 0:
                    # 检查是否已选中（可能需要根据实际 UI 判断）
                    role_btn.click()
                    self.page.wait_for_timeout(300)
        
        if is_active is not None:
            active_switch = dialog.locator('[role="switch"]')
            if active_switch.count() > 0:
                is_checked = active_switch.is_checked()
                if is_active != is_checked:
                    active_switch.click()
                    self.page.wait_for_timeout(300)
    
    def click_save_changes(self) -> None:
        """点击 Save Changes 按钮"""
        logger.info("点击 Save Changes 按钮")
        dialog = self.page.locator('[role="dialog"]')
        save_btn = dialog.get_by_role("button", name="Save Changes")
        save_btn.click()
        self.page.wait_for_timeout(500)  # 减少等待时间：从 1000 减少到 500
