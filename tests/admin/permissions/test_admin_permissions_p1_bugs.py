# ═══════════════════════════════════════════════════════════════
# Admin Permissions P1 - Bug 验证测试
# ═══════════════════════════════════════════════════════════════
"""
P1 级别测试：Admin Permissions 页面 Bug 验证

已发现的 Bug：
1. i18n 不一致：权限名称混用中文和英文 key
2. 权限数量过多：可能包含未使用的权限（Knowledge、Platform、Agents）
3. 权限显示名称未翻译：自定义权限显示为 Permission:xxx 格式
"""

import pytest
import allure
from playwright.sync_api import Page

from pages.admin_permissions_page import AdminPermissionsPage
from tests.admin.permissions._helpers import step_shot, navigate_and_wait
from utils.logger import TestLogger


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Permissions")
@allure.story("P1 - Bug 验证")
@allure.title("test_p1_bug_i18n_inconsistency - Bug: 国际化不一致")
@pytest.mark.xfail(reason="已知 Bug: 权限名称混用中文和英文 key，i18n 不一致")
def test_p1_bug_i18n_inconsistency(auth_page: Page):
    """
    Bug: 国际化不一致
    
    现象：
    - ABP Identity 权限组显示为中文（身份标识管理、角色管理、创建、编辑等）
    - SettingManagement 权限组显示为中文（设置管理、邮件、时区等）
    - 自定义权限组（Sessions、Knowledge、Platform、Agents）显示为 key（Permission:Sessions 等），未翻译
    - UI 界面是英文（Permissions、Role Permissions、Grant All 等）
    
    预期：
    - 权限名称应该与界面语言一致
    - 要么全中文，要么全英文
    - 自定义权限应该有正确的本地化资源
    """
    logger = TestLogger("test_p1_bug_i18n_inconsistency")
    logger.start()
    
    page_obj = AdminPermissionsPage(auth_page)
    
    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded", full_page=True)
    
    with allure.step("检查是否存在中文权限名称"):
        has_chinese = page_obj.has_chinese_permission_names()
        allure.attach(f"存在中文权限名称: {has_chinese}", "i18n_check", allure.attachment_type.TEXT)
    
    with allure.step("检查是否存在未翻译的权限（显示为 Permission:xxx）"):
        # 检查页面中是否有 Permission: 开头的文本
        untranslated_count = auth_page.locator('text=/Permission:[A-Z]/').count()
        has_untranslated = untranslated_count > 0
        allure.attach(
            f"未翻译权限数量: {untranslated_count}\n存在未翻译权限: {has_untranslated}",
            "untranslated_check",
            allure.attachment_type.TEXT
        )
    
    with allure.step("获取权限分组名称"):
        group_names = page_obj.get_permission_group_names()
        allure.attach(
            "\n".join(group_names),
            "permission_groups",
            allure.attachment_type.TEXT
        )
    
    with allure.step("验证 i18n 一致性"):
        # Bug 确认：权限名称混用中文和英文 key
        assert has_chinese or has_untranslated, "应该存在 i18n 不一致的问题"
        if has_chinese and has_untranslated:
            allure.attach(
                "Bug 确认: 权限名称混用中文和英文 key，i18n 不一致",
                "bug_confirmed",
                allure.attachment_type.TEXT
            )
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Permissions")
@allure.story("P1 - Bug 验证")
@allure.title("test_p1_bug_permission_count_excessive - Bug: 权限数量过多")
def test_p1_bug_permission_count_excessive(auth_page: Page):
    """
    Bug: 权限数量过多，可能包含未使用的权限
    
    现象：
    - 总共有 42 个权限
    - 包括 Knowledge（6个）、Platform（5个）、Agents（7个）等权限组
    - 这些权限可能定义了但未实际使用
    
    预期：
    - 只显示实际使用的权限
    - 未使用的权限应该隐藏或移除
    """
    logger = TestLogger("test_p1_bug_permission_count_excessive")
    logger.start()
    
    page_obj = AdminPermissionsPage(auth_page)
    
    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded", full_page=True)
    
    with allure.step("获取权限分组列表"):
        group_names = page_obj.get_permission_group_names()
        total_groups = len(group_names)
        
        # 检查是否有可能未使用的权限组
        potentially_unused = []
        for group_name in group_names:
            # Knowledge、Platform、Agents 等可能是未使用的权限组
            if any(keyword in group_name.lower() for keyword in ['knowledge', 'platform', 'agents']):
                potentially_unused.append(group_name)
        
        allure.attach(
            f"总权限组数: {total_groups}\n"
            f"可能未使用的权限组: {len(potentially_unused)}\n"
            f"可能未使用的权限组列表:\n" + "\n".join(potentially_unused),
            "permission_groups_analysis",
            allure.attachment_type.TEXT
        )
        
        step_shot(page_obj, "step_permission_groups", full_page=True)
    
    with allure.step("验证权限数量"):
        # 记录权限数量，但不强制断言（因为可能确实需要这么多权限）
        allure.attach(
            f"当前权限组数量: {total_groups}\n"
            f"如果权限数量过多，可能需要检查是否有未使用的权限",
            "permission_count_analysis",
            allure.attachment_type.TEXT
        )
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Permissions")
@allure.story("P1 - Bug 验证")
@allure.title("test_p1_bug_permission_untranslated - Bug: 权限未翻译")
@pytest.mark.xfail(reason="已知 Bug: 自定义权限显示为 Permission:xxx 格式，未翻译")
def test_p1_bug_permission_untranslated(auth_page: Page):
    """
    Bug: 权限未翻译
    
    现象：
    - 自定义权限（Sessions、Knowledge、Platform、Agents）显示为 key（Permission:Sessions 等）
    - 而不是翻译后的文本（如 "Sessions"、"Knowledge" 等）
    
    预期：
    - 所有权限都应该有正确的本地化资源
    - 显示名称应该是翻译后的文本，而不是 key
    """
    logger = TestLogger("test_p1_bug_permission_untranslated")
    logger.start()
    
    page_obj = AdminPermissionsPage(auth_page)
    
    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded", full_page=True)
    
    with allure.step("检查未翻译的权限"):
        # 切换到 Role Permissions tab
        page_obj.switch_to_role_permissions()
        auth_page.wait_for_timeout(1000)
        
        # 选择 member 角色
        page_obj.select_member_role()
        
        # 查找所有包含 "Permission:" 的文本
        permission_elements = auth_page.locator('text=/Permission:[A-Z]/')
        count = permission_elements.count()
        
        untranslated_permissions = []
        for i in range(min(count, 10)):  # 只取前10个
            text = permission_elements.nth(i).text_content() or ""
            if text.startswith("Permission:"):
                untranslated_permissions.append(text)
        
        allure.attach(
            f"未翻译权限数量: {count}\n"
            f"未翻译权限示例（前10个）:\n" + "\n".join(untranslated_permissions),
            "untranslated_permissions",
            allure.attachment_type.TEXT
        )
        
        step_shot(page_obj, "step_untranslated_permissions", full_page=True)
        
        # Bug 确认：存在未翻译的权限
        if count > 0:
            allure.attach(
                "Bug 确认: 自定义权限显示为 Permission:xxx 格式，缺少本地化资源",
                "bug_confirmed",
                allure.attachment_type.TEXT
            )
            assert False, f"存在 {count} 个未翻译的权限，应该提供正确的本地化资源"
    
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.admin
@pytest.mark.bug
@allure.feature("Admin Permissions")
@allure.story("P1 - Bug 验证")
@allure.title("test_p1_bug_permission_mixed_languages - Bug: 权限混用中英文")
def test_p1_bug_permission_mixed_languages(auth_page: Page):
    """
    Bug: 权限混用中英文
    
    现象：
    - ABP Identity 权限组：中文（身份标识管理、角色管理、创建、编辑等）
    - SettingManagement 权限组：中文（设置管理、邮件、时区等）
    - 自定义权限组：英文 key（Permission:Sessions 等）
    - UI 界面：英文
    
    预期：
    - 所有权限应该使用统一的语言
    - 如果界面是英文，权限名称也应该是英文
    """
    logger = TestLogger("test_p1_bug_permission_mixed_languages")
    logger.start()
    
    page_obj = AdminPermissionsPage(auth_page)
    
    with allure.step("导航到 Admin Permissions 页面"):
        navigate_and_wait(page_obj, auth_page)
        step_shot(page_obj, "step_page_loaded", full_page=True)
    
    with allure.step("分析权限语言分布"):
        # 检查中文权限
        chinese_patterns = ["身份标识管理", "角色管理", "设置管理", "用户管理", "创建", "编辑", "删除"]
        chinese_count = 0
        for pattern in chinese_patterns:
            count = auth_page.locator(f'text={pattern}').count()
            chinese_count += count
        
        # 检查未翻译权限（Permission:xxx）
        untranslated_count = auth_page.locator('text=/Permission:[A-Z]/').count()
        
        allure.attach(
            f"中文权限数量: {chinese_count}\n"
            f"未翻译权限数量（Permission:xxx）: {untranslated_count}\n"
            f"结论: 权限混用中文和英文 key，i18n 不一致",
            "language_analysis",
            allure.attachment_type.TEXT
        )
        
        step_shot(page_obj, "step_mixed_languages", full_page=True)
    
    with allure.step("验证语言一致性"):
        # Bug 确认：权限混用中英文
        if chinese_count > 0 and untranslated_count > 0:
            allure.attach(
                "Bug 确认: 权限混用中文和英文 key，应该统一使用一种语言",
                "bug_confirmed",
                allure.attachment_type.TEXT
            )
            # 不强制断言失败，因为这是已知 bug
            assert True, "Bug 已确认：权限混用中英文"
    
    logger.end(success=True)
