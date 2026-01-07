#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
页面对象：AdminUsersPage
目标：封装用户管理页面的稳定定位器与业务操作
原则：短小、直白、少分支
"""

from typing import List, Dict, Optional
import allure
from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# 页面对象：AdminUsersPage
# ============================================================
class AdminUsersPage(BasePage):
    """
    用户管理页面对象
    
    职责：
    - 封装稳定定位器（role/label/testid 优先）
    - 封装业务操作（search/create/edit/delete）
    - 提供断言辅助方法（不包含断言逻辑）
    """
    
    # ========================================
    # 页面配置
    # ========================================
    URL = "/admin/users"
    page_loaded_indicator = "role=table"  # 或 "[data-testid='users-table']"
    
    # ========================================
    # 定位器：搜索
    # ========================================
    SEARCH_INPUT = "[placeholder='Search...']"  # 根据实际页面
    # 备选：SEARCH_INPUT = "role=searchbox"
    # 备选：SEARCH_INPUT = "[data-testid='search-input']"
    
    # ========================================
    # 定位器：列表
    # ========================================
    USER_TABLE = "role=table"
    USER_ROWS = "role=table >> role=row"
    USER_HEADER = "role=table >> role=columnheader"
    EMPTY_STATE = "[data-testid='empty-state'], .ant-empty"
    
    # ========================================
    # 定位器：按钮
    # ========================================
    CREATE_BUTTON = "button:has-text('Create New User')"  # 根据实际页面
    # 备选：CREATE_BUTTON = "role=button[name='Create New User']"
    # 备选：CREATE_BUTTON = "[data-testid='create-user-btn']"
    
    EDIT_BUTTON = "role=button[name='Edit']"
    DELETE_BUTTON = "role=button[name='Delete']"
    
    # ========================================
    # 定位器：表单（基于实际页面截图）
    # ========================================
    # 对话框中的输入字段，使用 placeholder 定位
    USERNAME_INPUT = "input[placeholder='User name']"
    PASSWORD_INPUT = "input[placeholder='Password']"
    NAME_INPUT = "input[placeholder='Name']"
    SURNAME_INPUT = "input[placeholder='Surname']"
    EMAIL_INPUT = "input[placeholder='Email address']"
    PHONE_INPUT = "input[placeholder='Phone Number']"
    
    # 复选框（使用最简单的策略：通过可见文本附近的checkbox）
    # 注意：这两个复选框在页面中默认都是勾选状态
    ACTIVE_CHECKBOX_TEXT = "Active"
    LOCK_CHECKBOX_TEXT = "Lock account after failed login attempts"
    
    # 按钮（实际文本）
    SUBMIT_BUTTON = "button:has-text('Save')"
    CANCEL_BUTTON = "button:has-text('Cancel')"
    
    # ========================================
    # 定位器：对话框
    # ========================================
    # Create/Edit 对话框（使用 role=dialog）
    FORM_DIALOG = "role=dialog"
    
    # Delete 确认对话框（使用 role=alertdialog）
    DELETE_CONFIRM_DIALOG = "role=alertdialog"
    DELETE_YES_BUTTON = "role=alertdialog >> button:has-text('Yes')"
    DELETE_CANCEL_BUTTON = "role=alertdialog >> button:has-text('Cancel')"
    
    # 兼容旧代码
    CONFIRM_DIALOG = FORM_DIALOG
    CONFIRM_YES_BUTTON = DELETE_YES_BUTTON
    CONFIRM_NO_BUTTON = DELETE_CANCEL_BUTTON
    
    # ========================================
    # 定位器：提示消息
    # ========================================
    SUCCESS_MESSAGE = ".ant-message-success, .success-toast"
    ERROR_MESSAGE = ".ant-message-error, .error-toast"
    
    # ========================================
    # 基础方法
    # ========================================
    
    @allure.step("导航到用户管理页面")
    def navigate(self) -> None:
        """导航到用户管理页面"""
        self.goto(self.URL)
        self.wait_for_page_load()
        logger.info(f"导航到用户管理页面: {self.URL}")
    
    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        loaded = self.is_visible(self.page_loaded_indicator, timeout=5000)
        logger.debug(f"页面加载状态: {loaded}")
        return loaded
    
    # ========================================
    # 列表操作
    # ========================================
    
    @allure.step("获取用户列表")
    def get_user_list(self) -> List[str]:
        """
        获取用户列表（所有行的文本内容）
        
        Returns:
            List[str]: 用户列表，每项是一行的完整文本
        """
        try:
            rows = self.page.locator(self.USER_ROWS).all()
            # 过滤掉表头行
            users = [row.inner_text() for row in rows[1:] if row.is_visible()]
            logger.info(f"获取到 {len(users)} 个用户")
            return users
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []
    
    @allure.step("获取用户数量")
    def get_user_count(self) -> int:
        """获取用户数量"""
        count = len(self.get_user_list())
        logger.info(f"用户数量: {count}")
        return count
    
    @allure.step("检查用户是否可见: {username}")
    def is_user_visible(self, username: str) -> bool:
        """
        检查指定用户名是否在表格中可见
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否可见
        """
        # 只检查表格中的行，不检查toast提示等其他元素
        try:
            row = self.page.get_by_role("row").filter(has_text=username)
            visible = row.count() > 0 and row.first.is_visible()
        except Exception:
            visible = False
        logger.debug(f"用户 {username} 在表格中的可见性: {visible}")
        return visible
    
    @allure.step("检查空状态是否显示")
    def is_empty_state_visible(self) -> bool:
        """检查空状态提示是否显示"""
        return self.is_visible(self.EMPTY_STATE)
    
    # ========================================
    # 搜索操作
    # ========================================
    
    @allure.step("搜索用户: {query}")
    def search_user(self, query: str, use_type: bool = True) -> None:
        """
        搜索用户（支持实时搜索和回车触发两种方式）
        
        Args:
            query: 搜索关键词
            use_type: 是否使用逐字输入（触发实时搜索）。
                     True=逐字输入（适合正常搜索，触发onChange）
                     False=直接填充（适合特殊字符，如XSS/SQLi测试）
        """
        # 获取搜索输入框
        search_input = self.page.locator(self.SEARCH_INPUT)
        
        # 清空输入框
        search_input.clear()
        
        # 根据是否包含特殊字符选择输入方式
        has_special_chars = any(c in query for c in ["'", '"', '<', '>', ';', '--', '\\'])
        
        if use_type and not has_special_chars:
            # 逐字输入，触发onChange事件
            search_input.type(query, delay=50)
            # type()后等待一下让onChange事件触发
            self.page.wait_for_timeout(200)
        else:
            # 直接填充（用于特殊字符）
            self.fill(self.SEARCH_INPUT, query)
        
        # 按回车确保搜索触发（兼容回车触发的UI）
        search_input.press("Enter")
        
        # 等待搜索完成 - 多重等待策略确保结果加载完成
        # 1. 等待网络空闲（搜索API调用完成）
        try:
            self.page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            # 网络空闲可能不稳定，继续等待
            pass
        
        # 2. 固定等待确保UI渲染完成
        self.page.wait_for_timeout(1000)
        
        logger.info(f"搜索用户: {query}")
    
    @allure.step("清空搜索")
    def clear_search(self) -> None:
        """清空搜索框"""
        self.fill(self.SEARCH_INPUT, "")
        # 按回车键触发重新加载
        self.page.press(self.SEARCH_INPUT, "Enter")
        # 等待搜索结果更新
        try:
            self.page.wait_for_load_state('networkidle', timeout=3000)
        except Exception:
            pass
        # 额外等待UI渲染完成
        self.page.wait_for_timeout(500)
        logger.info("清空搜索")
    
    # ========================================
    # 创建用户操作
    # ========================================
    
    @allure.step("点击创建用户按钮")
    def click_create(self) -> None:
        """点击创建用户按钮，等待对话框出现"""
        self.click(self.CREATE_BUTTON)
        # 等待表单对话框出现（role=dialog）
        self.wait_for_element(self.FORM_DIALOG, state="visible", timeout=5000)
        logger.info("点击创建用户按钮，对话框已打开")
    
    @allure.step("填写用户表单")
    def fill_user_form(
        self,
        username: str,
        email: str,
        password: str,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        phone: Optional[str] = None,
        active: bool = True,
        lock_account: bool = False
    ) -> None:
        """
        填写用户表单（基于实际页面字段）
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            name: 名（可选）
            surname: 姓（可选）
            phone: 电话号码（可选）
            active: 是否激活（默认 True）
            lock_account: 登录失败后锁定账号（默认 False）
        """
        # 填写必填字段
        self.fill(self.USERNAME_INPUT, username)
        
        # 密码字段不记录日志
        self.page.fill(self.PASSWORD_INPUT, password)
        logger.debug(f"填写密码: ***")
        
        # 填写可选字段
        if name:
            self.fill(self.NAME_INPUT, name)
        
        if surname:
            self.fill(self.SURNAME_INPUT, surname)
        
        self.fill(self.EMAIL_INPUT, email)
        
        if phone:
            self.fill(self.PHONE_INPUT, phone)
        
        # 处理复选框（Active 和 Lock 默认都是勾选的）
        # 使用灵活的定位策略
        try:
            # Active 复选框：定位包含文本的父元素，然后找 checkbox
            active_checkbox = self.page.locator(f"text={self.ACTIVE_CHECKBOX_TEXT}").locator("..").locator("input[type='checkbox']").first
            active_checkbox.set_checked(active, timeout=3000)
            logger.debug(f"设置 Active 复选框: {active}")
        except Exception as e:
            logger.warning(f"设置 Active 复选框失败: {e}，跳过")
        
        try:
            # Lock 复选框：同样策略
            lock_checkbox = self.page.locator(f"text={self.LOCK_CHECKBOX_TEXT}").locator("..").locator("input[type='checkbox']").first
            lock_checkbox.set_checked(lock_account, timeout=3000)
            logger.debug(f"设置 Lock account 复选框: {lock_account}")
        except Exception as e:
            logger.warning(f"设置 Lock account 复选框失败: {e}，跳过")
        
        logger.info(f"填写用户表单: username={username}, email={email}, name={name}, surname={surname}")
    
    @allure.step("提交表单")
    def submit_form(self) -> None:
        """提交表单，等待对话框关闭"""
        self.click(self.SUBMIT_BUTTON)
        
        # 等待表单对话框关闭（使用try-catch，超时不阻塞）
        try:
            self.wait_for_element(self.FORM_DIALOG, state="hidden", timeout=3000)
            logger.info("提交表单完成，对话框已关闭")
        except Exception as e:
            logger.warning(f"等待对话框关闭超时，继续执行: {e}")
            # 等待一下让页面有时间响应
            self.page.wait_for_timeout(500)
        
        # 等待网络空闲（列表刷新）
        try:
            self.page.wait_for_load_state('networkidle', timeout=2000)
        except Exception:
            self.page.wait_for_timeout(300)
    
    @allure.step("取消表单")
    def cancel_form(self) -> None:
        """取消表单，等待对话框关闭"""
        self.click(self.CANCEL_BUTTON)
        # 等待表单对话框关闭（role=dialog）
        self.wait_for_element(self.FORM_DIALOG, state="hidden", timeout=5000)
        logger.info("取消表单，对话框已关闭")
    
    # ========================================
    # 编辑用户操作
    # ========================================
    
    @allure.step("点击编辑按钮: {username}")
    def click_edit(self, username: str) -> None:
        """
        点击指定用户的编辑按钮，等待编辑对话框出现
        
        Args:
            username: 用户名
        """
        # 找到包含用户名的行，使用filter而不是has-text伪选择器
        row = self.page.get_by_role("row").filter(has_text=username)
        # 点击该行的Actions按钮打开下拉菜单
        row.get_by_role("button", name="Actions").click()
        # 等待菜单出现
        self.page.wait_for_timeout(200)
        # 点击下拉菜单中的Edit按钮
        self.page.get_by_role("button", name="Edit").click()
        # 等待表单对话框出现（role=dialog）
        self.wait_for_element(self.FORM_DIALOG, state="visible", timeout=5000)
        logger.info(f"点击编辑按钮: {username}，对话框已打开")
    
    # ========================================
    # 删除用户操作
    # ========================================
    
    @allure.step("点击删除按钮: {username}")
    def click_delete(self, username: str) -> None:
        """
        点击指定用户的删除按钮
        
        Args:
            username: 用户名
        """
        # 找到包含用户名的行，使用filter而不是has-text伪选择器
        row = self.page.get_by_role("row").filter(has_text=username)
        # 点击该行的Actions按钮打开下拉菜单
        row.get_by_role("button", name="Actions").click()
        # 等待菜单出现
        self.page.wait_for_timeout(200)
        # 点击下拉菜单中的Delete按钮
        self.page.get_by_role("button", name="Delete").click()
        logger.info(f"点击删除按钮: {username}")
    
    @allure.step("确认删除")
    def confirm_delete(self) -> None:
        """在删除确认对话框中点击确认，等待对话框关闭"""
        # 使用专门的删除确认按钮（role=alertdialog >> button:has-text('Yes')）
        self.click(self.DELETE_YES_BUTTON)
        
        # 等待删除确认对话框关闭（使用try-catch，超时不阻塞）
        try:
            self.wait_for_element(self.DELETE_CONFIRM_DIALOG, state="hidden", timeout=3000)
            logger.info("确认删除，对话框已关闭")
        except Exception as e:
            logger.warning(f"等待对话框关闭超时，继续执行: {e}")
            # 等待一下让页面有时间响应
            self.page.wait_for_timeout(500)
        
        # 等待网络空闲（列表刷新）
        try:
            self.page.wait_for_load_state('networkidle', timeout=2000)
        except Exception:
            self.page.wait_for_timeout(300)
    
    @allure.step("取消删除")
    def cancel_delete(self) -> None:
        """在删除确认对话框中点击取消"""
        # 使用专门的删除取消按钮（role=alertdialog >> button:has-text('Cancel')）
        self.click(self.DELETE_CANCEL_BUTTON)
        logger.info("取消删除")
    
    # ========================================
    # 消息提示
    # ========================================
    
    def get_success_message(self) -> str:
        """获取成功提示消息"""
        if self.is_visible(self.SUCCESS_MESSAGE):
            msg = self.page.locator(self.SUCCESS_MESSAGE).inner_text()
            logger.info(f"成功消息: {msg}")
            return msg
        return ""
    
    def get_error_message(self) -> str:
        """获取错误提示消息"""
        if self.is_visible(self.ERROR_MESSAGE):
            msg = self.page.locator(self.ERROR_MESSAGE).inner_text()
            logger.warning(f"错误消息: {msg}")
            return msg
        return ""
