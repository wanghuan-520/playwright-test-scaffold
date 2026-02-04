# ═══════════════════════════════════════════════════════════════
# Admin Platform Settings Page Object
# ═══════════════════════════════════════════════════════════════
"""
Admin Platform Settings 页面对象
URL: http://localhost:5173/admin/settings
Type: PROTECTED (需要 admin 账号登录)
"""

from playwright.sync_api import Page
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class AdminSettingsPage(BasePage):
    """
    Admin Platform Settings 页面对象
    
    职责：封装 Platform Settings 页面元素和操作
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 页面标题
    PAGE_TITLE = 'h2:has-text("Platform Settings")'
    PAGE_SUBTITLE = 'text=Configure platform-wide settings'
    
    # Tab 选项卡
    TOOLS_MCP_TAB = 'button:has-text("Tools & MCP")'
    LLM_PROVIDERS_TAB = 'button:has-text("LLM Providers")'
    AGENTS_TAB = 'button:has-text("Agents")'
    ADVANCED_TAB = 'button:has-text("Advanced")'
    
    # Tools & MCP Tab
    RECONNECT_MCP_BUTTON = 'button:has-text("Reconnect MCP")'
    UPDATE_SKILLS_BUTTON = 'button:has-text("Update Skills")'
    SKILLSMP_MARKETPLACE_BUTTON = 'button:has-text("SkillsMP Marketplace")'
    TOOL_STATISTICS_TOTAL = 'text=Total'
    TOOL_STATISTICS_MCP = 'text=MCP'
    TOOL_STATISTICS_SKILLS = 'text=Skills'
    NO_TOOLS_MESSAGE = 'text=No tools available'
    
    # LLM Providers Tab
    DEFAULT_PROVIDER_SELECT = 'combobox'
    PROVIDER_LIST = 'button:has-text("DeepSeek"), button:has-text("OpenAI")'
    
    # Agents Tab
    NO_SESSION_MESSAGE = 'text=No Session Connected'
    
    # Advanced Tab
    SECRET_KEY_INPUT = 'input[placeholder*="OpenAI:ApiKey"]'
    SECRET_VALUE_INPUT = 'input[placeholder*="Enter secret value"]'
    SAVE_SECRET_BUTTON = 'button:has-text("Save Secret")'
    REMOVE_SECRET_BUTTON = 'button:has-text("Remove Secret")'
    
    # 页面 URL
    URL = 'http://localhost:5173/admin/settings'
    URL_PATH = '/admin/settings'
    
    # 页面加载标识
    page_loaded_indicator = 'h2:has-text("Platform Settings")'
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def navigate(self) -> None:
        """导航到 Platform Settings 页面"""
        logger.info("导航到 Admin Settings 页面")
        self.goto(self.URL, wait_for_load=False)
        self.wait_for_page_load()
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.is_visible(self.page_loaded_indicator, timeout=10000)
        except Exception:
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # TAB NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    
    def switch_to_tools_mcp(self) -> None:
        """切换到 Tools & MCP Tab"""
        self.page.get_by_role("button", name="Tools & MCP").click()
    
    def switch_to_llm_providers(self) -> None:
        """切换到 LLM Providers Tab"""
        self.page.get_by_role("button", name="LLM Providers").click()
    
    def switch_to_agents(self) -> None:
        """切换到 Agents Tab"""
        self.page.get_by_role("button", name="Agents").click()
    
    def switch_to_advanced(self) -> None:
        """切换到 Advanced Tab"""
        self.page.get_by_role("button", name="Advanced").click()
    
    # ═══════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════
    
    def is_reconnect_mcp_disabled(self) -> bool:
        """检查 Reconnect MCP 按钮是否禁用"""
        return self.page.locator(self.RECONNECT_MCP_BUTTON).is_disabled()
    
    def has_no_tools_message(self) -> bool:
        """检查是否显示 'No tools available' 消息"""
        return self.is_visible(self.NO_TOOLS_MESSAGE, timeout=3000)
    
    def is_ux_contradiction(self) -> bool:
        """
        检查 UX 矛盾：按钮禁用但提示让用户点击
        Bug: "Reconnect MCP" 禁用，但提示 "Try 'Reconnect MCP'"
        """
        button_disabled = self.is_reconnect_mcp_disabled()
        has_message = self.has_no_tools_message()
        return button_disabled and has_message

