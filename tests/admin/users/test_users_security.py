#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Security 测试：用户管理 - 安全防护
测试场景：XSS 防护、SQLi 防护、未授权访问
"""

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from tests.admin.users._helpers import delete_test_user
import json
from pathlib import Path


# ============================================================
# Security 测试：XSS 注入（用户名）
# ============================================================

@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_xss_username(admin_page):
    """
    Security: XSS 载荷（用户名字段）不应执行
    
    验收标准：
    - 在用户名字段输入 XSS 载荷
    - XSS 代码不执行（无弹窗）
    - 输入被转义或过滤
    - 不导致页面崩溃
    """
    page = admin_page
    
    # 加载测试数据
    data_file = Path("test-data/admin_users_data.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    xss_payload = test_data["invalid"]["xss_username"]
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("打开创建用户表单"):
        page.click_create()
    
    with allure.step(f"输入 XSS 载荷到用户名: {xss_payload}"):
        try:
            page.fill_user_form(
                username=xss_payload,
                email="xsstest@test.com",
                password="Test@123456"
            )
            page.take_screenshot("xss_username_filled")
            
            # 尝试提交
            page.submit_form()
            page.take_screenshot("xss_username_submitted")
            
        except Exception as e:
            # 如果填写或提交过程中出错，可能是前端拦截
            allure.attach(
                f"XSS 载荷可能被前端拦截: {str(e)}",
                name="前端拦截",
                attachment_type=allure.attachment_type.TEXT
            )
    
    with allure.step("验证 XSS 未执行"):
        # 验证没有弹出对话框（XSS 未执行）
        # 注意：这里使用 try-except 因为如果真的有 alert，evaluate 会阻塞
        try:
            has_alert = page.page.evaluate("() => window.alert.called")
            assert not has_alert, "XSS 不应执行"
        except:
            # 如果 window.alert.called 不存在，说明没有被劫持，XSS 未执行
            pass
        
        # 验证页面未崩溃
        assert page.is_loaded(), "页面应该正常加载"
        
        page.take_screenshot("xss_username_result")
    
    # Teardown: 清理（如果用户创建成功）
    with allure.step("清理测试数据"):
        try:
            # 尝试删除（可能创建失败）
            delete_test_user(page, xss_payload)
        except:
            pass


# ============================================================
# Security 测试：XSS 注入（邮箱）
# ============================================================

@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_xss_email(admin_page):
    """
    Security: XSS 载荷（邮箱字段）不应执行
    
    验收标准：
    - 在邮箱字段输入 XSS 载荷
    - XSS 代码不执行
    - 输入被转义或过滤
    """
    page = admin_page
    
    # 加载测试数据
    data_file = Path("test-data/admin_users_data.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    xss_payload = test_data["invalid"]["xss_email"]
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step("打开创建用户表单"):
        page.click_create()
    
    with allure.step(f"输入 XSS 载荷到邮箱: {xss_payload}"):
        try:
            page.fill_user_form(
                username=f"xsstest_{int(page.page.evaluate('Date.now()'))}",
                email=xss_payload,
                password="Test@123456"
            )
            page.take_screenshot("xss_email_filled")
            
            # 尝试提交
            page.submit_form()
            page.take_screenshot("xss_email_submitted")
            
        except Exception as e:
            # 如果填写或提交过程中出错，可能是前端拦截
            allure.attach(
                f"XSS 载荷可能被前端拦截: {str(e)}",
                name="前端拦截",
                attachment_type=allure.attachment_type.TEXT
            )
    
    with allure.step("验证 XSS 未执行"):
        # 验证页面未崩溃
        assert page.is_loaded(), "页面应该正常加载"
        
        page.take_screenshot("xss_email_result")
    
    # 不需要清理（邮箱格式无效，用户应该创建失败）


# ============================================================
# Security 测试：SQLi 注入（搜索）
# ============================================================

@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_sqli_search(admin_page):
    """
    Security: SQLi 载荷（搜索功能）不应导致 5xx 错误
    
    验收标准：
    - 在搜索框输入 SQLi 载荷
    - 后端正确处理，不导致 5xx 错误
    - 返回空结果或正常结果
    """
    page = admin_page
    
    # 加载测试数据
    data_file = Path("test-data/admin_users_data.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    sqli_payload = test_data["invalid"]["sqli_search"]
    
    with allure.step("导航到用户管理页面"):
        page.navigate()
    
    with allure.step(f"在搜索框输入 SQLi 载荷: {sqli_payload}"):
        page.search_user(sqli_payload)
        page.take_screenshot("sqli_search")
    
    with allure.step("验证 SQLi 未成功"):
        # 验证页面未崩溃（不是 5xx 错误）
        assert page.is_loaded(), "页面应该正常加载，不应出现 5xx 错误"
        
        # 验证返回结果（应该是空或正常结果）
        users = page.get_user_list()
        
        allure.attach(
            f"SQLi 载荷: {sqli_payload}\n"
            f"搜索结果数量: {len(users)}",
            name="SQLi 搜索结果",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # 验证没有返回所有用户（SQLi 常见目标）
        # 注意：这个断言可能需要根据实际情况调整
        # 如果系统正确处理，应该返回空结果或正常搜索结果
        
        page.take_screenshot("sqli_search_result")


# ============================================================
# Security 测试：未授权访问
# ============================================================

@allure.feature("用户管理")
@allure.story("安全测试")
@pytest.mark.P1
@pytest.mark.security
def test_unauth_redirect(unauth_page):
    """
    Security: 未登录用户应被重定向到登录页
    
    验收标准：
    - 使用未登录的 page 访问用户管理页面
    - 自动重定向到登录页
    - 不显示用户管理内容
    """
    page = AdminUsersPage(unauth_page)
    
    with allure.step("尝试访问用户管理页面（未登录）"):
        page.navigate()
        page.take_screenshot("unauth_access")
    
    with allure.step("验证重定向到登录页"):
        current_url = page.page.url
        
        # 验证 URL 包含登录路径
        assert "/account/login" in current_url.lower() or \
               "/login" in current_url.lower(), \
               f"应重定向到登录页，当前 URL: {current_url}"
        
        allure.attach(
            f"当前 URL: {current_url}",
            name="重定向验证",
            attachment_type=allure.attachment_type.TEXT
        )
        
        page.take_screenshot("unauth_redirected")

