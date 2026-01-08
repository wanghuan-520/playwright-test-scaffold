# ═══════════════════════════════════════════════════════════════
# BasePage Unit Tests
# ═══════════════════════════════════════════════════════════════
"""BasePage 单元测试

测试目标：
- 页面导航方法
- 元素操作方法
- 截图功能

使用 Mock 替代真实 Playwright
"""

import pytest
from unittest.mock import MagicMock, patch


class TestBasePageNavigation:
    """BasePage 导航测试"""

    @pytest.fixture
    def mock_page(self):
        """创建 Mock Playwright Page"""
        page = MagicMock()
        page.url = "http://localhost:3000/test"
        page.goto = MagicMock()
        page.reload = MagicMock()
        page.go_back = MagicMock()
        page.go_forward = MagicMock()
        page.wait_for_load_state = MagicMock()
        page.wait_for_selector = MagicMock()
        page.wait_for_timeout = MagicMock()
        page.screenshot = MagicMock(return_value=b"fake_screenshot")
        return page

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager"""
        with patch('core.base_page.ConfigManager') as mock:
            config_instance = MagicMock()
            config_instance.get_service_url.return_value = "http://localhost:3000"
            mock.return_value = config_instance
            yield mock

    def test_goto_with_path(self, mock_page, mock_config):
        """goto 方法：相对路径"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            URL = "/test"
            def navigate(self):
                self.goto(self.URL)
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        page_obj.goto("/test", wait_for_load=False)

        mock_page.goto.assert_called_once()
        call_args = mock_page.goto.call_args
        assert "/test" in call_args[0][0]

    def test_goto_with_full_url(self, mock_page, mock_config):
        """goto 方法：完整 URL"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            URL = "/test"
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        page_obj.goto("https://example.com/page", wait_for_load=False)

        mock_page.goto.assert_called_once()
        call_args = mock_page.goto.call_args
        assert "https://example.com/page" in call_args[0][0]

    def test_refresh(self, mock_page, mock_config):
        """refresh 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            page_loaded_indicator = "body"
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        page_obj.refresh()

        mock_page.reload.assert_called_once()


class TestBasePageQueries:
    """BasePage 查询方法测试"""

    @pytest.fixture
    def mock_page(self):
        """创建 Mock Playwright Page"""
        page = MagicMock()
        page.is_visible = MagicMock(return_value=True)
        page.is_enabled = MagicMock(return_value=True)
        page.is_checked = MagicMock(return_value=False)
        page.text_content = MagicMock(return_value="Test Text")
        page.input_value = MagicMock(return_value="Test Value")
        page.get_attribute = MagicMock(return_value="attr_value")
        page.title = MagicMock(return_value="Page Title")
        return page

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager"""
        with patch('core.base_page.ConfigManager') as mock:
            config_instance = MagicMock()
            config_instance.get_service_url.return_value = "http://localhost:3000"
            mock.return_value = config_instance
            yield mock

    def test_is_visible(self, mock_page, mock_config):
        """is_visible 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        result = page_obj.is_visible("#selector")

        assert result is True
        mock_page.is_visible.assert_called_once()

    def test_is_enabled(self, mock_page, mock_config):
        """is_enabled 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        result = page_obj.is_enabled("#button")

        assert result is True
        mock_page.is_enabled.assert_called_with("#button")

    def test_get_text(self, mock_page, mock_config):
        """get_text 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        result = page_obj.get_text("#element")

        assert result == "Test Text"
        mock_page.text_content.assert_called_once()

    def test_get_input_value(self, mock_page, mock_config):
        """get_input_value 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        result = page_obj.get_input_value("#input")

        assert result == "Test Value"
        mock_page.input_value.assert_called_with("#input")

    def test_get_title(self, mock_page, mock_config):
        """get_title 方法"""
        from core.base_page import BasePage

        class TestPage(BasePage):
            def navigate(self):
                pass
            def is_loaded(self):
                return True

        page_obj = TestPage(mock_page)
        result = page_obj.get_title()

        assert result == "Page Title"
        mock_page.title.assert_called_once()


class TestBaseDialog:
    """BaseDialog 测试"""

    @pytest.fixture
    def mock_page(self):
        """创建 Mock Playwright Page"""
        page = MagicMock()
        page.is_visible = MagicMock(return_value=True)
        page.keyboard = MagicMock()
        return page

    @pytest.fixture
    def mock_config(self):
        """Mock ConfigManager"""
        with patch('core.base_page.ConfigManager') as mock:
            config_instance = MagicMock()
            config_instance.get_service_url.return_value = "http://localhost:3000"
            mock.return_value = config_instance
            yield mock

    def test_dialog_is_loaded(self, mock_page, mock_config):
        """对话框加载检查"""
        from core.base_page import BaseDialog

        class TestDialog(BaseDialog):
            DIALOG_SELECTOR = ".test-dialog"

        dialog = TestDialog(mock_page)
        result = dialog.is_loaded()

        assert result is True
        mock_page.is_visible.assert_called()

    def test_dialog_navigate_noop(self, mock_page, mock_config):
        """对话框 navigate 是空操作"""
        from core.base_page import BaseDialog

        class TestDialog(BaseDialog):
            DIALOG_SELECTOR = ".test-dialog"

        dialog = TestDialog(mock_page)
        
        # 不应该抛出异常
        dialog.navigate()
