#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
辅助函数：用户管理测试
功能：创建、清理测试用户
"""

import re
import time
from typing import Dict, Optional
import allure
from pages.admin_users_page import AdminUsersPage
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# ABP Constants (从 profile_settings 复用)
# ============================================================

# ============================================================
# 测试用已知用户数据（从账号池获取，避免硬编码）
# ============================================================
KNOWN_ADMIN_USER = "TestAdmin1"
KNOWN_ADMIN_EMAIL = "test_admin1@test.com"
KNOWN_MEMBER_USER = "loadtest_user_001"
KNOWN_MEMBER_EMAIL = "loadtest_user_001@testmail.com"


class AbpUserConsts:
    """
    ABP IdentityUserConsts 默认值
    
    参考：
    - ABP Framework IdentityUserConsts
    - Swagger UpdateProfileDto
    """
    # 长度限制
    MaxUserNameLength = 256
    MaxEmailLength = 256
    MaxNameLength = 64
    MaxSurnameLength = 64
    MaxPhoneNumberLength = 16
    MaxPasswordLength = 128
    MinPasswordLength = 6
    
    # 正则模式
    # ABP 默认用户名允许：字母数字 + @ . _ -
    UserNamePattern = r"^[a-zA-Z0-9@\._\-]+$"
    
    # 最小可用 email 正则（用于 sanity）
    EmailPattern = r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$"


# ============================================================
# 测试数据生成
# ============================================================

def generate_unique_user(prefix: str = "test") -> Dict[str, str]:
    """
    生成唯一的测试用户数据
    
    Args:
        prefix: 用户名前缀
        
    Returns:
        Dict: 包含 username, email, password 的字典
    """
    timestamp = int(time.time())
    user_data = {
        "username": f"{prefix}_{timestamp}",
        "email": f"{prefix}_{timestamp}@test.com",
        "password": "Test@123456"
    }
    logger.info(f"生成测试用户: {user_data['username']}")
    return user_data


# ============================================================
# 用户创建和清理
# ============================================================

def create_test_user(
    page: AdminUsersPage,
    user_data: Dict[str, str],
    name: Optional[str] = None,
    surname: Optional[str] = None
) -> None:
    """
    通过 UI 创建测试用户
    
    Args:
        page: AdminUsersPage 实例
        user_data: 用户数据（username, email, password）
        name: 名（可选）
        surname: 姓（可选）
    """
    username = user_data["username"]
    
    with allure.step(f"创建测试用户: {username}"):
        # 确保已导航到 admin/users 页面
        if page.page.url != page.URL and not page.page.url.endswith(page.URL_PATH):
            page.navigate()
        # 确保页面基本元素已加载（不等待数据，因为可能没有用户）
        page.is_loaded()
        # 确保 Add User 按钮可见（快速检查）
        page.page.wait_for_selector('button:has-text("Add User")', state="visible", timeout=3000)
        page.click_add_user()
        # 等待对话框打开（快速检查）
        page.page.wait_for_selector('[role="dialog"] h2:has-text("Create New User")', state="visible", timeout=2000)
        page.fill_create_user_form(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            first_name=name or "",
            last_name=surname or ""
        )
        page.click_create_user()
        # 等待对话框关闭（快速检查）
        try:
            page.page.wait_for_selector('[role="dialog"]', state="hidden", timeout=2000)
        except Exception:
            # 如果对话框没有关闭，可能是创建失败，快速等待
            page.page.wait_for_timeout(300)
        page.page.wait_for_timeout(300)  # 大幅减少等待时间
        logger.info(f"创建测试用户成功: {username}")


def delete_test_user(page: AdminUsersPage, username: str) -> None:
    """
    通过 UI 删除测试用户
    
    Args:
        page: AdminUsersPage 实例
        username: 用户名
    """
    with allure.step(f"删除测试用户: {username}"):
        try:
            # 确保已导航到 admin/users 页面
            if page.page.url != page.URL and not page.page.url.endswith(page.URL_PATH):
                page.navigate()
            
            # 确保页面已加载
            page.is_loaded()
            
            # 关闭可能打开的对话框
            try:
                dialog = page.page.locator('[role="dialog"]')
                if dialog.is_visible(timeout=1000):
                    # 尝试点击 Cancel 或关闭按钮
                    cancel_btn = page.page.locator('[role="dialog"] button:has-text("Cancel")')
                    if cancel_btn.is_visible(timeout=500):
                        cancel_btn.click()
                    else:
                        # 尝试点击 X 按钮
                        close_btn = page.page.locator('[role="dialog"] button:has([class*="close"])')
                        if close_btn.is_visible(timeout=500):
                            close_btn.click()
                    page.page.wait_for_timeout(300)  # 等待对话框关闭
            except Exception:
                pass  # 如果没有对话框，继续执行
            
            # 先搜索用户（确保在当前页）
            # 使用更短的超时，避免长时间等待已删除的用户
            try:
                page.search_user(username)
                page.wait_for_filter_results(timeout=2000)  # 使用 wait_for_filter_results 代替固定等待
            except Exception:
                # 如果搜索超时，可能用户已删除
                logger.warning(f"搜索用户 {username} 超时，可能已删除")
                return
            
            # 检查用户是否存在
            try:
                user_count = page.get_visible_user_count()
                if user_count == 0:
                    logger.warning(f"用户不存在，无需删除: {username}")
                    return
                
                # 验证是否真的是这个用户（避免部分匹配）
                rows = page.page.locator('table tbody tr')
                found = False
                for i in range(min(rows.count(), 5)):  # 只检查前5行
                    row_text = rows.nth(i).text_content() or ""
                    if username in row_text:
                        found = True
                        break
                
                if not found:
                    logger.warning(f"搜索结果中未找到用户 {username}，可能已删除")
                    return
            except Exception:
                # 如果检查失败，可能用户已删除
                logger.warning(f"检查用户 {username} 时出错，可能已删除")
                return
            
            # 点击 Actions 按钮并删除
            page.click_user_action(username)
            page.page.wait_for_timeout(300)  # 减少等待时间
            
            # 点击 Delete User
            page.page.get_by_role("menuitem", name="Delete User").click()
            page.page.wait_for_timeout(300)  # 减少等待时间
            
            # 确认删除
            page.page.get_by_role("button", name="Delete").click()
            page.page.wait_for_timeout(500)  # 减少等待时间
            
            logger.info(f"删除测试用户成功: {username}")
            
        except Exception as e:
            logger.error(f"删除测试用户失败: {username}, 错误: {e}")
            # 不抛出异常，避免影响测试清理


# ============================================================
# Fixture 辅助函数
# ============================================================

def cleanup_test_users(page: AdminUsersPage, usernames: list) -> None:
    """
    批量清理测试用户
    
    Args:
        page: AdminUsersPage 实例
        usernames: 要清理的用户名列表
    """
    if not usernames:
        logger.info("没有需要清理的用户")
        return
    
    logger.info(f"开始清理 {len(usernames)} 个测试用户")
    
    for username in usernames:
        delete_test_user(page, username)
    
    logger.info("测试用户清理完成")


# ============================================================
# 工具函数
# ============================================================

def now_suffix() -> str:
    """生成时间戳后缀（毫秒级）"""
    return str(int(time.time() * 1000))


def is_valid_username(username: str) -> bool:
    """验证用户名是否符合 ABP 规则"""
    if not username:
        return False
    if len(username) > AbpUserConsts.MaxUserNameLength:
        return False
    return bool(re.match(AbpUserConsts.UserNamePattern, username))


def is_valid_email(email: str) -> bool:
    """验证邮箱格式（简化版）"""
    if not email:
        return False
    if len(email) > AbpUserConsts.MaxEmailLength:
        return False
    return bool(re.match(AbpUserConsts.EmailPattern, email))


def step_shot(page_obj, name: str, *, full_page: bool = False) -> None:
    """关键步骤截图（Allure 附件）"""
    try:
        screenshot = page_obj.page.screenshot(full_page=full_page)
        allure.attach(screenshot, name, allure.attachment_type.PNG)
    except Exception:
        pass


def get_cell_by_column_name(row, page, column_name: str) -> str:
    """
    按列名获取表格行中对应单元格的文本。
    不依赖硬编码列索引，而是通过 thead 列名动态定位。

    Args:
        row: Playwright locator 指向 <tr>
        page: Playwright Page 对象
        column_name: 列名（如 "ROLE", "STATUS", "EMAIL"）

    Returns:
        单元格文本（strip 后）
    """
    # 获取所有列头
    headers = page.locator('table thead th').all_text_contents()
    # 查找目标列的索引（忽略大小写）
    target_idx = -1
    for i, h in enumerate(headers):
        if column_name.upper() in h.upper():
            target_idx = i
            break
    if target_idx < 0:
        return ""
    # 按索引取对应 td
    cell = row.locator("td").nth(target_idx)
    return (cell.text_content() or "").strip() if cell.count() > 0 else ""

