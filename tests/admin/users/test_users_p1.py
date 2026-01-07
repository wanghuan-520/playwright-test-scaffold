#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P1 测试：用户管理 - 核心功能
测试场景：创建、编辑、删除用户（基础功能）

注意：
- 字段验证已迁移到矩阵测试（test_users_p1_*_matrix.py）
- 本文件只保留基础 CRUD 操作
"""

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import (
    generate_unique_user,
    create_test_user,
    delete_test_user
)
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================
# P1 测试：创建用户（基础功能）
# ============================================================

@allure.feature("用户管理")
@allure.story("创建用户")
@pytest.mark.P1
def test_create_user_valid(admin_page):
    """
    P1: 创建有效用户
    
    验收标准：
    - 填写所有必填字段
    - 提交成功
    - 用户出现在列表中
    """
    page = admin_page
    user_data = generate_unique_user("testuser")
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step(f"创建用户: {user_data['username']}"):
        create_test_user(page, user_data)
    
    with allure.step("验证用户已创建"):
        page.search_user(user_data["username"])
        page.take_screenshot("user_in_list_verified")
        assert page.is_user_visible(user_data["username"]), f"用户应在列表中: {user_data['username']}"
    
    # Teardown: 清理测试用户
    with allure.step("清理测试用户"):
        delete_test_user(page, user_data["username"])


# ============================================================
# P1 测试：删除用户
# ============================================================

@allure.feature("用户管理")
@allure.story("删除用户")
@pytest.mark.P1
def test_delete_user(admin_page):
    """
    P1: 删除用户
    
    验收标准：
    - 先创建用户
    - 删除用户
    - 确认删除
    - 用户从列表中消失
    
    已知问题：
    - 定位器问题，对话框遮挡
    """
    page = admin_page
    user_data = generate_unique_user("testuser")
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step(f"创建测试用户: {user_data['username']}"):
        create_test_user(page, user_data)
        
        # 验证创建成功
        page.search_user(user_data["username"])
        assert page.is_user_visible(user_data["username"]), "用户应创建成功"
    
    with allure.step(f"删除用户: {user_data['username']}"):
        page.click_delete(user_data["username"])
        page.confirm_delete()
    
    with allure.step("验证用户已删除"):
        page.search_user(user_data["username"])
        page.take_screenshot("user_deleted_verified")
        assert not page.is_user_visible(user_data["username"]), "用户应从列表中消失"


# ============================================================
# 已迁移的测试
# ============================================================

# ✅ 以下测试已迁移到矩阵测试，覆盖更全面：
#
# Username 验证 → test_users_p1_username_matrix.py (16 场景)
#   - test_create_user_duplicate_username
#   - 必填验证
#   - 格式验证
#   - 长度边界
#   - 特殊字符
#   - SQL注入/XSS
#
# Email 验证 → test_users_p1_email_matrix.py (13 场景)
#   - test_create_user_duplicate_email
#   - test_create_user_invalid_email
#   - 必填验证
#   - 格式验证
#   - 长度边界
#
# Password 验证 → test_users_p1_password_matrix.py (15 场景)
#   - test_create_user_weak_password
#   - 必填验证
#   - 强度验证
#   - 长度边界
#
# Name 验证 → test_users_p1_name_matrix.py (10 场景)
#   - 可选字段
#   - 格式验证
#   - 长度边界
#
# Surname 验证 → test_users_p1_surname_matrix.py (10 场景)
#   - 可选字段
#   - 格式验证
#   - 长度边界
#
# Phone 验证 → test_users_p1_phone_matrix.py (10 场景)
#   - 可选字段
#   - 格式验证
#   - 长度边界
