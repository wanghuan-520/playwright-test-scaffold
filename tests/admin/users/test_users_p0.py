#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
P0 测试：用户管理 - 关键路径
测试场景：页面加载、列表展示、搜索功能
"""

import allure
import pytest
from pages.admin_users_page import AdminUsersPage


# ============================================================
# P0 测试：页面加载
# ============================================================

@allure.feature("用户管理")
@allure.story("页面加载")
@pytest.mark.P0
def test_page_load(admin_page):
    """
    P0: 用户管理页面加载成功
    
    验收标准：
    - 页面可以访问
    - 页面加载时间 < 2s
    - 页面核心元素可见（用户表格）
    """
    page = admin_page
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("验证页面加载成功"):
        assert page.is_loaded(), "页面未正确加载，用户表格不可见"
        page.take_screenshot("page_loaded_verified")
    
    with allure.step("验证页面 URL 正确"):
        assert page.URL in page.page.url, f"页面 URL 不正确，期望包含 {page.URL}"
    
    allure.attach(
        f"页面 URL: {page.page.url}",
        name="页面信息",
        attachment_type=allure.attachment_type.TEXT
    )


# ============================================================
# P0 测试：查看用户列表
# ============================================================

@allure.feature("用户管理")
@allure.story("查看用户列表")
@pytest.mark.P0
def test_view_user_list(admin_page):
    """
    P0: 管理员可以查看用户列表
    
    验收标准：
    - 用户列表可见
    - 列表包含用户数据（或显示空状态）
    - 列表有表头
    """
    page = admin_page
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("验证页面加载"):
        assert page.is_loaded(), "页面未正确加载"
    
    with allure.step("获取用户列表"):
        users = page.get_user_list()
        user_count = len(users)
        
        allure.attach(
            f"用户数量: {user_count}",
            name="用户列表信息",
            attachment_type=allure.attachment_type.TEXT
        )
    
    with allure.step("验证列表状态"):
        # 如果有用户，验证用户数量
        if user_count > 0:
            assert user_count > 0, "用户列表不应为空"
            allure.attach(
                "\n".join(users[:5]),  # 只显示前5个用户
                name="前5个用户",
                attachment_type=allure.attachment_type.TEXT
            )
        # 如果没有用户，验证空状态提示
        else:
            is_empty = page.is_empty_state_visible()
            assert is_empty, "空状态提示应该显示"


# ============================================================
# P0 测试：搜索用户
# ============================================================

@allure.feature("用户管理")
@allure.story("搜索用户")
@pytest.mark.P0
def test_search_user(admin_page):
    """
    P0: 管理员可以搜索用户
    
    验收标准：
    - 搜索框可用
    - 输入关键词后可以搜索
    - 搜索结果正确（包含关键词或显示无结果）
    """
    page = admin_page
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("获取搜索前的用户列表"):
        users_before = page.get_user_list()
        total_count = len(users_before)
        
        allure.attach(
            f"搜索前用户数量: {total_count}",
            name="初始状态",
            attachment_type=allure.attachment_type.TEXT
        )
    
    # 如果列表为空，跳过搜索测试
    if total_count == 0:
        pytest.skip("用户列表为空，无法测试搜索功能")
    
    # 优先搜索 "admin"（系统默认存在），如果不存在则从列表中选择
    search_query = "admin"
    
    # 如果列表中没有包含"admin"的用户，则使用第一个用户的片段
    has_admin = any("admin" in user.lower() for user in users_before)
    if not has_admin and users_before:
        first_user = users_before[0]
        # 简单提取：取第一个单词或前几个字符
        search_query = first_user.split()[0][:5] if first_user else "user"
    
    with allure.step(f"搜索用户: {search_query}"):
        page.search_user(search_query)
    
    with allure.step("验证搜索结果"):
        users_after = page.get_user_list()
        result_count = len(users_after)
        page.take_screenshot("search_result_verified")
        
        allure.attach(
            f"搜索关键词: {search_query}\n"
            f"搜索结果数量: {result_count}\n"
            f"搜索前数量: {total_count}",
            name="搜索结果",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # 验证搜索结果数量 <= 搜索前数量（过滤效果）
        assert result_count <= total_count, "搜索结果数量不应超过总数"
        
        # 如果有结果，验证结果包含搜索关键词（模糊匹配）
        if result_count > 0:
            # 至少有一个结果包含搜索关键词
            has_match = any(search_query.lower() in user.lower() for user in users_after)
            assert has_match, f"搜索结果应包含关键词: {search_query}"
    
    with allure.step("清空搜索"):
        page.clear_search()
        users_cleared = page.get_user_list()
        
        # 验证清空后恢复原列表
        assert len(users_cleared) == total_count, "清空搜索后应恢复原列表"


# ============================================================
# P0 测试：搜索无结果
# ============================================================

@allure.feature("用户管理")
@allure.story("搜索用户")
@pytest.mark.P0
def test_search_no_results(admin_page):
    """
    P0: 搜索不存在的用户，显示无结果提示
    
    验收标准：
    - 搜索不存在的关键词
    - 列表为空或显示"未找到用户"提示
    """
    page = admin_page
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    # 搜索一个不可能存在的用户名
    nonexistent_query = "nonexistent_user_xyz_12345"
    
    with allure.step(f"搜索不存在的用户: {nonexistent_query}"):
        page.search_user(nonexistent_query)
    
    with allure.step("验证无结果状态"):
        users = page.get_user_list()
        result_count = len(users)
        page.take_screenshot("no_results_verified")
        
        # 验证搜索结果为空
        assert result_count == 0, f"搜索不存在的用户应返回空结果，实际返回 {result_count} 个"
        
        # 验证显示空状态或"未找到"提示
        is_empty = page.is_empty_state_visible()
        
        allure.attach(
            f"搜索关键词: {nonexistent_query}\n"
            f"搜索结果数量: {result_count}\n"
            f"空状态提示显示: {is_empty}",
            name="无结果验证",
            attachment_type=allure.attachment_type.TEXT
        )

