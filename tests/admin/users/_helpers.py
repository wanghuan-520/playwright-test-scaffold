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
        page.click_create()
        page.fill_user_form(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            name=name,
            surname=surname
        )
        page.submit_form()
        # 截图验证创建结果
        page.take_screenshot(f"user_created_{username}")
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
            # 先搜索用户（确保在当前页）
            page.search_user(username)
            
            # 检查用户是否存在
            if not page.is_user_visible(username):
                logger.warning(f"用户不存在，无需删除: {username}")
                return
            
            # 删除用户
            page.click_delete(username)
            page.confirm_delete()
            # 截图验证删除结果
            page.take_screenshot(f"user_deleted_{username}")
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

