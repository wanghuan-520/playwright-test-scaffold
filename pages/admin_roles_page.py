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
    ROLE_CARD_ACTIONS_BUTTON = 'button:has(svg)'  # Actions 按钮（每个卡片右上角的按钮）
    ROLE_ACTIONS_MENU = '[role="menu"]'  # Actions 菜单
    ROLE_ACTIONS_MENU_EDIT = '[role="menuitem"]:has-text("Edit Role")'  # Edit Role 菜单项
    ROLE_ACTIONS_MENU_PERMISSIONS = '[role="menuitem"]:has-text("Manage Permissions")'  # Manage Permissions 菜单项
    ROLE_ACTIONS_MENU_DELETE = '[role="menuitem"]:has-text("Delete Role")'  # Delete Role 菜单项
    
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
        try:
            cards = self.page.locator(self.ROLE_CARD).all()
            return len(cards)
        except Exception:
            return 0
    
    def wait_for_roles_loaded(self, timeout: int = 10000) -> bool:
        """等待角色列表加载（支持空状态）"""
        try:
            # 等待页面加载完成（标题可见）
            self.page.wait_for_selector(self.PAGE_TITLE, state="visible", timeout=5000)
            
            # 等待 API 调用完成 - 等待角色卡片或空状态出现
            try:
                # 等待角色卡片出现，或者等待空状态消息
                self.page.wait_for_selector(
                    f'{self.ROLE_CARD}, text=No roles, text=No roles found, text=Empty',
                    state="visible",
                    timeout=timeout
                )
                return True
            except Exception:
                # 如果超时，检查是否有任何内容
                has_cards = self.page.locator(self.ROLE_CARD).count() > 0
                has_empty_state = (
                    self.page.locator('text=No roles').count() > 0 or
                    self.page.locator('text=No roles found').count() > 0 or
                    self.page.locator('text=Empty').count() > 0
                )
                return has_cards or has_empty_state
        except Exception as e:
            logger.warning(f"等待角色列表加载时出错: {e}")
            # 即使出错，也检查是否有卡片
            try:
                return self.page.locator(self.ROLE_CARD).count() > 0
            except Exception:
                return False
    
    def get_role_user_count(self, role_name: str) -> str:
        """获取特定角色的用户数量文本"""
        try:
            # 查找包含角色名的卡片
            card = self.page.locator(f'h3:has-text("{role_name}")').locator('xpath=ancestor::div[contains(@class, "cursor-pointer")]')
            if card.count() == 0:
                return ""
            # 查找用户数量文本
            user_text = card.locator('text=/\\d+ Users/').first.text_content(timeout=3000)
            return user_text or ""
        except Exception:
            return ""
    
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
    
    def _find_role_card(self, role_name: str):
        """
        查找角色卡片（内部方法）
        
        Returns:
            tuple: (role_heading, matched_text, card_container) 或 None
        """
        # 等待角色列表加载
        self.wait_for_roles_loaded(timeout=15000)
        
        # 额外等待，确保 API 调用完成
        self.page.wait_for_timeout(3000)
        
        # 先查找所有 h3 元素（角色名称）
        all_h3_elements = []
        try:
            # 等待至少一个 h3 元素出现
            self.page.wait_for_selector('h3', state="visible", timeout=10000)
            all_h3 = self.page.locator('h3').all()
            for h3 in all_h3:
                try:
                    text = h3.text_content(timeout=1000) or ""
                    if text.strip():
                        all_h3_elements.append((h3, text.strip()))
                except Exception:
                    continue
        except Exception:
            # 如果等待超时，尝试直接查找
            all_h3 = self.page.locator('h3').all()
            for h3 in all_h3:
                try:
                    text = h3.text_content(timeout=1000) or ""
                    if text.strip():
                        all_h3_elements.append((h3, text.strip()))
                except Exception:
                    continue
        
        if len(all_h3_elements) == 0:
            raise Exception(f"找不到任何角色卡片（页面可能未加载角色列表）")
        
        # 尝试通过文本内容匹配（不区分大小写，支持部分匹配）
        role_heading = None
        matched_text = None
        role_name_lower = role_name.lower().strip()
        
        for h3, text in all_h3_elements:
            text_lower = text.lower()
            # 精确匹配或部分匹配
            if text_lower == role_name_lower or role_name_lower in text_lower:
                role_heading = h3
                matched_text = text
                logger.info(f"找到角色: {text} (匹配 {role_name})")
                break
        
        if role_heading is None:
            # 列出所有可用的角色名称
            available_roles = [text for _, text in all_h3_elements[:15]]
            raise Exception(f"找不到角色卡片: {role_name}。可用角色: {', '.join(available_roles) if available_roles else '无'}")
        
        # 查找卡片容器
        try:
            card_container = role_heading.locator('xpath=ancestor::div[contains(@class, "cursor-pointer")]').first
            if card_container.count() > 0:
                return (role_heading, matched_text, card_container)
        except Exception:
            pass
        
        return (role_heading, matched_text, None)
    
    def click_role_card(self, role_name: str) -> None:
        """点击特定角色卡片（已废弃：直接点击卡片不会打开对话框）"""
        logger.warning("click_role_card 已废弃：角色卡片点击不会打开对话框，请使用 open_role_edit_dialog 或 open_role_permissions_dialog")
        role_heading, matched_text, card_container = self._find_role_card(role_name)
        
        if card_container:
            card_container.click()
            logger.info(f"点击角色卡片容器: {matched_text}")
        else:
            role_heading.click()
    
    def open_role_actions_menu(self, role_name: str) -> None:
        """
        打开角色 Actions 菜单
        
        Args:
            role_name: 角色名称
        """
        logger.info(f"打开角色 Actions 菜单: {role_name}")
        role_heading, matched_text, card_container = self._find_role_card(role_name)
        
        if not card_container:
            raise Exception(f"找不到角色卡片容器: {role_name}")
        
        # 在卡片容器内查找 Actions 按钮（button with svg）
        actions_button = card_container.locator('button:has(svg)').first
        if actions_button.count() == 0:
            raise Exception(f"找不到 Actions 按钮: {role_name}")
        
        actions_button.click()
        self.page.wait_for_timeout(500)  # 等待菜单打开
        logger.info(f"已打开 Actions 菜单: {matched_text}")
    
    def open_role_edit_dialog(self, role_name: str) -> None:
        """
        打开 Edit Role 对话框
        
        Args:
            role_name: 角色名称
        """
        logger.info(f"打开 Edit Role 对话框: {role_name}")
        self.open_role_actions_menu(role_name)
        
        # 点击 "Edit Role" 菜单项
        edit_menu_item = self.page.locator(self.ROLE_ACTIONS_MENU_EDIT).first
        if edit_menu_item.count() == 0:
            raise Exception(f"找不到 'Edit Role' 菜单项: {role_name}")
        
        # 等待菜单项可见
        edit_menu_item.wait_for(state="visible", timeout=3000)
        edit_menu_item.click()
        self.page.wait_for_timeout(500)  # 等待对话框打开
        logger.info(f"已打开 Edit Role 对话框: {role_name}")
    
    def open_role_permissions_dialog(self, role_name: str) -> None:
        """
        打开 Role Permissions 对话框
        
        Args:
            role_name: 角色名称
        """
        logger.info(f"打开 Role Permissions 对话框: {role_name}")
        self.open_role_actions_menu(role_name)
        
        # 点击 "Manage Permissions" 菜单项
        permissions_menu_item = self.page.locator(self.ROLE_ACTIONS_MENU_PERMISSIONS).first
        if permissions_menu_item.count() == 0:
            raise Exception(f"找不到 'Manage Permissions' 菜单项: {role_name}")
        
        # 等待菜单项可见
        permissions_menu_item.wait_for(state="visible", timeout=3000)
        permissions_menu_item.click()
        self.page.wait_for_timeout(500)  # 等待对话框打开
        logger.info(f"已打开 Role Permissions 对话框: {role_name}")
    
    # ═══════════════════════════════════════════════════════════════
    # CREATE ROLE DIALOG
    # ═══════════════════════════════════════════════════════════════
    
    # Create Role 对话框选择器
    CREATE_ROLE_DIALOG = '[role="dialog"]:has-text("Create Role")'
    CREATE_ROLE_NAME_INPUT = 'input[placeholder="Enter role name"]'
    CREATE_ROLE_DEFAULT_SWITCH = '[role="dialog"] [role="switch"] >> nth=0'
    CREATE_ROLE_PUBLIC_SWITCH = '[role="dialog"] [role="switch"] >> nth=1'
    CREATE_ROLE_CANCEL_BUTTON = '[role="dialog"] button:has-text("Cancel")'
    CREATE_ROLE_SUBMIT_BUTTON = '[role="dialog"] button:has-text("Create Role")'
    
    def wait_for_create_role_dialog(self, timeout: int = 5000) -> bool:
        """等待 Create Role 对话框打开"""
        try:
            self.page.wait_for_selector(self.CREATE_ROLE_DIALOG, state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    
    def fill_create_role_form(
        self,
        name: str,
        is_default: bool = False,
        is_public: bool = True
    ) -> None:
        """填写 Create Role 表单"""
        logger.info(f"填写 Create Role 表单: name={name}, is_default={is_default}, is_public={is_public}")
        
        # Role Name
        self.fill(self.CREATE_ROLE_NAME_INPUT, name)
        
        # Default Role switch
        default_switch = self.page.locator(self.CREATE_ROLE_DEFAULT_SWITCH).first
        current_default = default_switch.get_attribute("aria-checked")
        if (current_default == "true") != is_default:
            default_switch.click()
        
        # Public Role switch
        public_switch = self.page.locator(self.CREATE_ROLE_PUBLIC_SWITCH).first
        current_public = public_switch.get_attribute("aria-checked")
        if (current_public == "true") != is_public:
            public_switch.click()
    
    def submit_create_role(self) -> None:
        """提交 Create Role 表单"""
        logger.info("提交 Create Role 表单")
        self.click(self.CREATE_ROLE_SUBMIT_BUTTON)
    
    def cancel_create_role(self) -> None:
        """取消 Create Role 对话框"""
        logger.info("取消 Create Role 对话框")
        self.click(self.CREATE_ROLE_CANCEL_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # EDIT ROLE DIALOG
    # ═══════════════════════════════════════════════════════════════
    
    # Edit Role 对话框选择器
    EDIT_ROLE_DIALOG = '[role="dialog"]:has-text("Edit Role")'
    EDIT_ROLE_NAME_INPUT = '[role="dialog"] input:not([type="checkbox"])'  # Role Name 输入框（Static role 可能是 disabled）
    EDIT_ROLE_DEFAULT_SWITCH = '[role="dialog"] [role="switch"] >> nth=0'
    EDIT_ROLE_PUBLIC_SWITCH = '[role="dialog"] [role="switch"] >> nth=1'
    EDIT_ROLE_CANCEL_BUTTON = '[role="dialog"] button:has-text("Cancel")'
    EDIT_ROLE_SAVE_BUTTON = '[role="dialog"] button:has-text("Save"), [role="dialog"] button:has-text("Update"), [role="dialog"] button:has-text("Save Changes")'
    
    def wait_for_edit_role_dialog(self, timeout: int = 5000) -> bool:
        """等待 Edit Role 对话框打开"""
        try:
            self.page.wait_for_selector(self.EDIT_ROLE_DIALOG, state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    
    def fill_edit_role_form(
        self,
        name: str = None,
        is_default: bool = None,
        is_public: bool = None
    ) -> None:
        """填写 Edit Role 表单"""
        logger.info(f"填写 Edit Role 表单: name={name}, is_default={is_default}, is_public={is_public}")
        
        # Role Name
        if name is not None:
            self.fill(self.EDIT_ROLE_NAME_INPUT, name)
        
        # Default Role switch
        if is_default is not None:
            default_switch = self.page.locator(self.EDIT_ROLE_DEFAULT_SWITCH).first
            current_default = default_switch.get_attribute("aria-checked")
            if (current_default == "true") != is_default:
                default_switch.click()
        
        # Public Role switch
        if is_public is not None:
            public_switch = self.page.locator(self.EDIT_ROLE_PUBLIC_SWITCH).first
            current_public = public_switch.get_attribute("aria-checked")
            if (current_public == "true") != is_public:
                public_switch.click()
    
    def submit_edit_role(self) -> None:
        """提交 Edit Role 表单"""
        logger.info("提交 Edit Role 表单")
        self.click(self.EDIT_ROLE_SAVE_BUTTON)
    
    def cancel_edit_role(self) -> None:
        """取消 Edit Role 对话框"""
        logger.info("取消 Edit Role 对话框")
        self.click(self.EDIT_ROLE_CANCEL_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # ROLE PERMISSIONS DIALOG
    # ═══════════════════════════════════════════════════════════════
    
    # Role Permissions 对话框选择器
    ROLE_PERMISSIONS_DIALOG = '[role="dialog"]:has-text("Permissions"), [role="dialog"]:has-text("Role Permissions")'
    ROLE_PERMISSIONS_CHECKBOX = '[role="dialog"] input[type="checkbox"]'
    ROLE_PERMISSIONS_GRANT_ALL_BUTTON = '[role="dialog"] button:has-text("Grant All"), [role="dialog"] button:has-text("Select All")'
    ROLE_PERMISSIONS_REVOKE_ALL_BUTTON = '[role="dialog"] button:has-text("Revoke All"), [role="dialog"] button:has-text("Deselect All")'
    ROLE_PERMISSIONS_SAVE_BUTTON = '[role="dialog"] button:has-text("Save"), [role="dialog"] button:has-text("Save Permissions")'
    ROLE_PERMISSIONS_CANCEL_BUTTON = '[role="dialog"] button:has-text("Cancel")'
    
    def wait_for_role_permissions_dialog(self, timeout: int = 5000) -> bool:
        """等待 Role Permissions 对话框打开"""
        try:
            self.page.wait_for_selector(self.ROLE_PERMISSIONS_DIALOG, state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    
    def get_permission_checkboxes(self):
        """获取所有权限复选框"""
        return self.page.locator(self.ROLE_PERMISSIONS_CHECKBOX).all()
    
    def toggle_permission(self, permission_name: str, grant: bool = True) -> None:
        """切换权限状态"""
        logger.info(f"切换权限: {permission_name}, grant={grant}")
        # 根据权限名称查找对应的 checkbox
        checkbox = self.page.locator(f'[role="dialog"]:has-text("{permission_name}") input[type="checkbox"]').first
        is_checked = checkbox.is_checked()
        if (is_checked != grant):
            checkbox.click()
    
    def grant_all_permissions(self) -> None:
        """授予所有权限"""
        logger.info("授予所有权限")
        self.click(self.ROLE_PERMISSIONS_GRANT_ALL_BUTTON)
    
    def revoke_all_permissions(self) -> None:
        """撤销所有权限"""
        logger.info("撤销所有权限")
        self.click(self.ROLE_PERMISSIONS_REVOKE_ALL_BUTTON)
    
    def save_role_permissions(self) -> None:
        """保存角色权限"""
        logger.info("保存角色权限")
        self.click(self.ROLE_PERMISSIONS_SAVE_BUTTON)
    
    def cancel_role_permissions(self) -> None:
        """取消 Role Permissions 对话框"""
        logger.info("取消 Role Permissions 对话框")
        self.click(self.ROLE_PERMISSIONS_CANCEL_BUTTON)
    
    # ═══════════════════════════════════════════════════════════════
    # DELETE ROLE DIALOG (UI)
    # ═══════════════════════════════════════════════════════════════

    DELETE_ROLE_DIALOG = '[role="dialog"]:has-text("Delete Role")'
    DELETE_ROLE_DIALOG_TITLE = '[role="dialog"] h2:has-text("Delete Role?")'
    DELETE_ROLE_DIALOG_WARNING = '[role="dialog"]:has-text("Users assigned to this role will lose their permissions")'
    DELETE_ROLE_DIALOG_CANCEL = '[role="dialog"] button:has-text("Cancel")'
    DELETE_ROLE_DIALOG_CONFIRM = '[role="dialog"] button:has-text("Delete Role")'

    def is_delete_role_menu_disabled(self, role_name: str) -> bool:
        """
        检查指定角色的 Delete Role 菜单项是否被禁用

        Args:
            role_name: 角色名称

        Returns:
            bool: True 表示 disabled，False 表示可点击
        """
        logger.info(f"检查角色 Delete Role 菜单项状态: {role_name}")
        self.open_role_actions_menu(role_name)

        delete_item = self.page.locator(self.ROLE_ACTIONS_MENU_DELETE).first
        if delete_item.count() == 0:
            raise Exception(f"找不到 'Delete Role' 菜单项: {role_name}")

        is_disabled = delete_item.is_disabled()
        # 关闭菜单
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        return is_disabled

    def open_delete_role_dialog(self, role_name: str) -> None:
        """
        打开 Delete Role 确认对话框

        Args:
            role_name: 角色名称
        """
        logger.info(f"打开 Delete Role 对话框: {role_name}")
        self.open_role_actions_menu(role_name)

        delete_item = self.page.locator(self.ROLE_ACTIONS_MENU_DELETE).first
        if delete_item.count() == 0:
            raise Exception(f"找不到 'Delete Role' 菜单项: {role_name}")

        delete_item.wait_for(state="visible", timeout=3000)
        delete_item.click()
        self.page.wait_for_timeout(500)
        logger.info(f"已打开 Delete Role 对话框: {role_name}")

    def wait_for_delete_role_dialog(self, timeout: int = 5000) -> bool:
        """等待 Delete Role 确认对话框打开"""
        try:
            self.page.wait_for_selector(self.DELETE_ROLE_DIALOG, state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def confirm_delete_role(self) -> None:
        """点击确认删除按钮"""
        logger.info("确认删除角色")
        self.click(self.DELETE_ROLE_DIALOG_CONFIRM)

    def cancel_delete_role(self) -> None:
        """点击取消删除按钮"""
        logger.info("取消删除角色")
        self.click(self.DELETE_ROLE_DIALOG_CANCEL)

    # ═══════════════════════════════════════════════════════════════
    # DELETE ROLE (API)
    # ═══════════════════════════════════════════════════════════════
    
    def delete_role_by_name(self, role_name: str) -> bool:
        """
        通过角色名称删除角色（通过 API）
        
        Args:
            role_name: 角色名称
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 先获取角色列表，找到角色的 ID
            # 获取后端 URL（通过前端 URL 推断，或使用配置）
            backend_url = self.config.get_service_url("backend") or self.URL.replace('/admin/roles', '').replace('5173', '5678')
            response = self.page.request.get(
                f"{backend_url}/api/identity/roles?MaxResultCount=1000",
                headers={"Accept": "application/json"}
            )
            
            if response.status != 200:
                logger.warning(f"获取角色列表失败，状态码: {response.status}")
                return False
            
            roles = response.json().get("items", [])
            role_id = None
            for role in roles:
                if role.get("name", "").lower() == role_name.lower():
                    role_id = role.get("id")
                    break
            
            if not role_id:
                logger.warning(f"找不到角色: {role_name}")
                return False
            
            # 删除角色
            # 获取后端 URL（通过前端 URL 推断，或使用配置）
            backend_url = self.config.get_service_url("backend") or self.URL.replace('/admin/roles', '').replace('5173', '5678')
            delete_response = self.page.request.delete(
                f"{backend_url}/api/identity/roles/{role_id}",
                headers={"Accept": "application/json"}
            )
            
            if delete_response.status in [200, 204]:
                logger.info(f"成功删除角色: {role_name} (ID: {role_id})")
                return True
            else:
                logger.warning(f"删除角色失败，状态码: {delete_response.status}")
                return False
                
        except Exception as e:
            logger.warning(f"删除角色时出错: {e}")
            return False

