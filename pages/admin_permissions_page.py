# ═══════════════════════════════════════════════════════════════
# Admin Permissions Page Object
# ═══════════════════════════════════════════════════════════════
"""
Admin Permissions 页面对象
URL: http://localhost:5173/admin/permissions
Type: PROTECTED (需要 admin 账号登录)

页面结构（via Playwright MCP 2026-02-11 重新定位）：
┌─────────────────────────────────────────────────────────┐
│  Permissions                                             │
│  Manage permissions for role, user                       │
│  ┌──────────────────┬──────────────────────────────────┐ │
│  │ [Role Permissions]│ [User Permissions]               │ │
│  ├──────────────────┴──────────────────────────────────┤ │
│  │ Select Role  3items│ {role} Permissions  N granted   │ │
│  │                    │ [Grant All] [Revoke All]        │ │
│  │  [test]            │ [Collapse All] [Save]          │ │
│  │  [member]          │ [Search permissions...]         │ │
│  │  [admin]           │                                │ │
│  │                    │ ▼ 身份标识管理  0/11            │ │
│  │                    │   ☐ 角色管理                    │ │
│  │                    │   ☐ 创建 ...                    │ │
│  │                    │ ▼ 设置管理  0/3                 │ │
│  │                    │ ▼ Permission:Sessions  0/10     │ │
│  │                    │ ▼ Permission:Knowledge 0/6      │ │
│  │                    │ ...                             │ │
│  └────────────────────┴────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

User Permissions Tab 左侧面板额外有：
  - searchbox "Search users..."
  - 用户列表（全量展示，用户少时无 Load more 按钮）
"""

from __future__ import annotations

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminPermissionsPage(BasePage):
    """Admin Permissions 页面对象"""

    # ═══════════════════════════════════════════════════════════════
    # SELECTORS（全部经过 Playwright MCP 验证）
    # ═══════════════════════════════════════════════════════════════

    # 页面标题
    PAGE_TITLE = 'h2:has-text("Permissions")'
    PAGE_SUBTITLE = 'text=/Manage permissions for role/i'

    # Tab 选项卡（role="tab"）
    ROLE_PERMISSIONS_TAB = '[role="tab"]:has-text("Role Permissions")'
    USER_PERMISSIONS_TAB = '[role="tab"]:has-text("User Permissions")'

    # 角色选择器（Role Tab 左侧面板）
    ROLE_SELECTOR = 'text=Select Role'
    MEMBER_ROLE_BUTTON = 'button:has-text("member")'
    ADMIN_ROLE_BUTTON = 'button:has-text("admin")'

    # 权限操作按钮
    GRANT_ALL_BUTTON = 'button:has-text("Grant All")'
    REVOKE_ALL_BUTTON = 'button:has-text("Revoke All")'
    COLLAPSE_ALL_BUTTON = 'button:has-text("Collapse All")'
    EXPAND_ALL_BUTTON = 'button:has-text("Expand All")'
    SAVE_BUTTON = 'button:has-text("Save")'

    # 权限搜索框（searchbox，兼容英文/中文 placeholder）
    SEARCH_INPUT = '[role="searchbox"][placeholder*="Search permissions"]'
    SEARCH_INPUT_I18N = '[role="searchbox"][placeholder*="搜索权限"]'

    # 用户选择器（User Tab 左侧面板）
    USER_SELECTOR = 'text=Select User'
    USER_SEARCH_INPUT = '[role="searchbox"][placeholder*="Search users"]'
    USER_SEARCH_INPUT_I18N = '[role="searchbox"][placeholder*="搜索用户"]'
    LOAD_MORE_BUTTON = 'button:has-text("Load more")'
    LOAD_MORE_BUTTON_I18N = 'button:has-text("加载更多")'

    # 统计文本
    GRANTED_COUNT = 'text=/\\d+ granted/'
    UNSAVED_COUNT = 'text=/\\d+ unsaved/'

    # 权限分组（按钮文本含 "x/y" 格式）
    IDENTITY_MANAGEMENT_GROUP = 'button:has-text("身份标识管理")'
    SETTINGS_MANAGEMENT_GROUP = 'button:has-text("设置管理")'

    # 页面 URL
    URL = 'http://localhost:5173/admin/permissions'
    URL_PATH = '/admin/permissions'
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
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False

    def wait_for_permissions_loaded(self, timeout: int = 20000) -> bool:
        """等待权限数据加载完成（Loading 消失且权限分组出现）"""
        try:
            # 等待 Loading 文本消失
            try:
                self.page.wait_for_selector('text=Loading...', state="hidden", timeout=timeout)
            except Exception:
                pass
            # 等待 Tab 可见（核心锚点：Tab 渲染即表明数据已加载）
            self.page.wait_for_selector(self.ROLE_PERMISSIONS_TAB, state="visible", timeout=timeout)
            # 等待至少一个权限分组按钮出现（文本含 "/"）
            self.page.wait_for_selector('button:has-text("/")', state="visible", timeout=10000)
            return True
        except Exception as e:
            logger.warning(f"等待权限数据加载超时: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # TAB ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def switch_to_role_permissions(self) -> None:
        """切换到角色权限 Tab"""
        logger.info("切换到 Role Permissions Tab")
        tab = self.page.locator(self.ROLE_PERMISSIONS_TAB)
        tab.wait_for(state="visible", timeout=10000)
        tab.click()
        self.page.wait_for_timeout(1500)
        # 等待 "Select Role" 出现确认面板已渲染
        self.page.locator(self.ROLE_SELECTOR).wait_for(state="visible", timeout=10000)

    def switch_to_user_permissions(self) -> None:
        """切换到用户权限 Tab（带重试 + 等待用户搜索框出现确认面板完全渲染）"""
        logger.info("切换到 User Permissions Tab")
        tab = self.page.locator(self.USER_PERMISSIONS_TAB)
        tab.wait_for(state="visible", timeout=10000)

        for attempt in range(3):
            tab.click()
            self.page.wait_for_timeout(1500)
            if self.is_user_permissions_tab_selected():
                break
            logger.warning(f"User Tab click 未生效 (attempt {attempt + 1})，重试...")
            self.page.wait_for_timeout(500)

        # 等待 "Select User" 出现
        self.page.locator(self.USER_SELECTOR).wait_for(state="visible", timeout=15000)
        # 关键：等待用户搜索框出现（确认面板完全渲染，而非仅标题切换）
        user_search = self.page.get_by_placeholder("Search users", exact=False).or_(
            self.page.get_by_placeholder("搜索用户", exact=False)
        )
        user_search.first.wait_for(state="visible", timeout=10000)

    def is_role_permissions_tab_selected(self) -> bool:
        tab = self.page.locator(self.ROLE_PERMISSIONS_TAB)
        return tab.get_attribute("aria-selected") == "true" if tab.count() > 0 else False

    def is_user_permissions_tab_selected(self) -> bool:
        tab = self.page.locator(self.USER_PERMISSIONS_TAB)
        return tab.get_attribute("aria-selected") == "true" if tab.count() > 0 else False

    # ═══════════════════════════════════════════════════════════════
    # ROLE SELECTION
    # ═══════════════════════════════════════════════════════════════

    def select_role(self, role_name: str) -> None:
        """选择指定角色"""
        logger.info(f"选择角色: {role_name}")
        btn = self.page.get_by_role("button", name=role_name, exact=True)
        btn.click()
        self.page.wait_for_timeout(1500)

    def select_member_role(self) -> None:
        self.select_role("member")

    def select_admin_role(self) -> None:
        self.select_role("admin")

    def get_role_count(self) -> int:
        """获取角色数量（从 '3 items' 文本中提取）"""
        try:
            items_text = self.page.locator('text=/\\d+ items/').first.text_content(timeout=2000) or ""
            return int(items_text.split()[0]) if items_text else 0
        except Exception:
            return 0

    # ═══════════════════════════════════════════════════════════════
    # USER SELECTION
    # ═══════════════════════════════════════════════════════════════

    def select_user(self, username: str) -> None:
        """选择指定用户"""
        logger.info(f"选择用户: {username}")
        btn = self.page.get_by_role("button", name=username, exact=True)
        btn.click()
        self.page.wait_for_timeout(1500)

    def _get_user_search_input(self):
        """获取用户搜索框（兼容 i18n placeholder）"""
        loc = self.page.get_by_placeholder("Search users", exact=False).or_(
            self.page.get_by_placeholder("搜索用户", exact=False)
        )
        loc.first.wait_for(state="visible", timeout=10000)
        return loc.first

    def search_user(self, keyword: str) -> None:
        """在 User Permissions 用户列表中搜索"""
        logger.info(f"搜索用户: {keyword}")
        self._get_user_search_input().fill(keyword)
        self.page.wait_for_timeout(2000)

    def clear_user_search(self) -> None:
        """清空用户搜索框"""
        self._get_user_search_input().fill("")
        self.page.wait_for_timeout(1000)

    def click_load_more(self) -> None:
        """点击 Load more 加载更多用户（兼容英文/中文按钮）"""
        load_btn = self.page.locator(self.LOAD_MORE_BUTTON).or_(
            self.page.locator(self.LOAD_MORE_BUTTON_I18N)
        )
        load_btn.first.click()
        self.page.wait_for_timeout(2000)

    # ═══════════════════════════════════════════════════════════════
    # PERMISSION ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def click_grant_all(self) -> None:
        logger.info("点击 Grant All")
        self.click(self.GRANT_ALL_BUTTON)
        self.page.wait_for_timeout(500)

    def click_revoke_all(self) -> None:
        logger.info("点击 Revoke All")
        self.click(self.REVOKE_ALL_BUTTON)
        self.page.wait_for_timeout(500)

    def click_collapse_all(self) -> None:
        logger.info("点击 Collapse All")
        self.click(self.COLLAPSE_ALL_BUTTON)
        self.page.wait_for_timeout(500)

    def click_expand_all(self) -> None:
        logger.info("点击 Expand All")
        self.click(self.EXPAND_ALL_BUTTON)
        self.page.wait_for_timeout(500)

    def click_save(self) -> None:
        logger.info("点击 Save 按钮")
        self.click(self.SAVE_BUTTON)

    def is_save_button_enabled(self) -> bool:
        save_btn = self.page.locator(self.SAVE_BUTTON).first
        if save_btn.count() == 0:
            return False
        return save_btn.is_enabled()

    def _get_permission_search_input(self):
        """右侧权限搜索框（Role Tab / User Tab 共用，兼容 i18n）"""
        loc = self.page.get_by_placeholder("Search permissions", exact=False).or_(
            self.page.get_by_placeholder("搜索权限", exact=False)
        )
        loc.first.wait_for(state="visible", timeout=15000)
        return loc.first

    def search_permissions(self, keyword: str) -> None:
        logger.info(f"搜索权限: {keyword}")
        self._get_permission_search_input().fill(keyword)
        self.page.wait_for_timeout(500)

    def clear_permission_search(self) -> None:
        self._get_permission_search_input().fill("")
        self.page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # PERMISSION GROUP ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def get_permission_group_names(self) -> list[str]:
        """获取所有权限分组按钮的文本（格式如 '身份标识管理 0/11'）"""
        # 权限分组按钮的文本包含 "数字/数字"
        buttons = self.page.locator('button:has-text("/")').all()
        names = []
        for btn in buttons:
            try:
                text = (btn.text_content(timeout=1000) or "").strip()
                # 确认是权限分组按钮（包含 x/y 模式）
                if "/" in text and any(c.isdigit() for c in text):
                    names.append(text)
            except Exception:
                continue
        return names

    def toggle_permission_group(self, group_keyword: str) -> None:
        """展开/折叠权限分组"""
        logger.info(f"切换权限分组: {group_keyword}")
        btn = self.page.locator(f'button:has-text("{group_keyword}")').first
        if btn.count() > 0:
            btn.click()
            self.page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # PERMISSION CHECKBOX ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def get_visible_checkbox_count(self) -> int:
        """获取当前可见的 checkbox 数量"""
        all_cb = self.page.get_by_role("checkbox").all()
        return len([cb for cb in all_cb if cb.is_visible()])

    def toggle_permission_by_label(self, label: str) -> None:
        """通过标签文本切换权限 checkbox"""
        logger.info(f"切换权限: {label}")
        cb = self.page.get_by_role("checkbox", name=label)
        if cb.count() > 0:
            cb.first.click()
            self.page.wait_for_timeout(300)

    def is_permission_checked(self, label: str) -> bool:
        """检查指定权限是否已勾选"""
        cb = self.page.get_by_role("checkbox", name=label)
        if cb.count() == 0:
            return False
        return cb.first.is_checked()

    # ═══════════════════════════════════════════════════════════════
    # STATS EXTRACTION
    # ═══════════════════════════════════════════════════════════════

    def get_granted_count_text(self) -> str:
        """获取 granted 计数文本（如 '48 granted'）"""
        try:
            el = self.page.locator(self.GRANTED_COUNT).first
            return (el.text_content(timeout=2000) or "").strip() if el.count() > 0 else ""
        except Exception:
            return ""

    def get_granted_number(self) -> int:
        """从 granted 文本中提取数字"""
        text = self.get_granted_count_text()
        try:
            return int(text.split()[0])
        except (ValueError, IndexError):
            return -1

    def get_permissions_count(self) -> int:
        """获取 '48 permissions' 中的数字"""
        try:
            el = self.page.locator('text=/\\d+ permissions?/').first
            text = (el.text_content(timeout=2000) or "").strip()
            return int(text.split()[0])
        except Exception:
            return -1

    def get_items_count(self) -> int:
        """获取左侧 'N items' 中的数字（角色数或用户数）"""
        try:
            el = self.page.locator('text=/\\d+ items?/').first
            text = (el.text_content(timeout=2000) or "").strip()
            return int(text.split()[0])
        except Exception:
            return -1

    def has_unsaved_changes(self) -> bool:
        return self.page.locator(self.UNSAVED_COUNT).count() > 0

    def get_child_checkbox_states(self, parent_label: str) -> list[tuple[str, bool]]:
        """获取父权限下所有子 checkbox 的 (name, checked) 列表"""
        results = []
        all_cb = self.page.get_by_role("checkbox").all()
        capture = False
        for cb in all_cb:
            try:
                name = cb.get_attribute("aria-label") or ""
                if not cb.is_visible():
                    continue
                # 父节点匹配
                if name == parent_label:
                    capture = True
                    continue
                # 遇到下一个非子节点（不以 ├ └ 开头）则停止
                if capture:
                    if name.startswith("├") or name.startswith("└"):
                        checked = cb.is_checked()
                        clean_name = name.lstrip("├└ ").strip()
                        results.append((clean_name, checked))
                    else:
                        break
            except Exception:
                continue
        return results

    def get_user_button_names(self) -> list[str]:
        """获取 User Tab 左侧面板中所有用户按钮名称"""
        buttons = self.page.locator('text=Select User').locator(
            'xpath=following::button'
        ).all()
        names = []
        for btn in buttons[:50]:
            try:
                text = (btn.text_content(timeout=500) or "").strip()
                if text and not text.startswith("Load more") and text not in (
                    "Grant All", "Revoke All", "Collapse All", "Expand All", "Save",
                ):
                    names.append(text)
            except Exception:
                continue
        return names

    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════

    def has_chinese_permission_names(self) -> bool:
        chinese_patterns = ["身份标识管理", "角色管理", "设置管理", "用户管理"]
        for pattern in chinese_patterns:
            if self.page.locator(f'text={pattern}').count() > 0:
                return True
        return False
