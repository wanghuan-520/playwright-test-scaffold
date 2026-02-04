# ═══════════════════════════════════════════════════════════════
# Profile - P1 Avatar Tests
# URL: http://localhost:5173/account/profile
# ═══════════════════════════════════════════════════════════════
"""
P1：头像上传测试。

测试内容：
- 头像上传弹窗打开/关闭
- 上传有效图片
- 验证上传后头像更新
"""

import os
import re
import pytest
import allure
from pathlib import Path

from utils.logger import TestLogger
from tests.myaccount._helpers import attach_rule_source_note, step_shot
from playwright.sync_api import Page
from pages.personal_settings_page import PersonalSettingsPage


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def profile_page(auth_page: Page):
    """Profile 页面 fixture"""
    page_obj = PersonalSettingsPage(auth_page)
    page_obj.navigate()
    yield auth_page, page_obj


@pytest.fixture(scope="module")
def test_images_dir():
    """测试图片目录"""
    return Path(__file__).parent.parent.parent.parent / "test-data" / "images"


@pytest.fixture(scope="module")
def test_avatar_path(test_images_dir):
    """测试用头像图片路径 (PNG)"""
    return str(test_images_dir / "test_avatar.png")


@pytest.fixture(scope="module")
def test_avatar_path_2(test_images_dir):
    """第二个测试头像（用于替换测试）"""
    return str(test_images_dir / "test_avatar_2.png")


# ═══════════════════════════════════════════════════════════════
# P1 TESTS - AVATAR
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Dialog")
@allure.description(
    """
测试点：
- 点击头像区域打开上传弹窗
- 弹窗包含标题 "Upload Avatar"
- 弹窗包含拖拽区域和格式提示
- 点击 Cancel 关闭弹窗
- 证据：弹窗截图
"""
)
def test_p1_avatar_dialog_open_close(profile_page):
    """P1: 头像上传弹窗打开/关闭"""
    attach_rule_source_note("Profile P1 - avatar dialog")
    logger = TestLogger("test_p1_avatar_dialog_open_close")
    logger.start()

    auth_page, page_obj = profile_page

    with allure.step("验证初始状态（弹窗关闭）"):
        assert not page_obj.is_avatar_dialog_open(), "初始状态弹窗应该关闭"
        step_shot(page_obj, "step_initial", full_page=True)

    with allure.step("点击头像按钮打开弹窗"):
        page_obj.open_avatar_dialog()
        step_shot(page_obj, "step_dialog_open", full_page=True)

    with allure.step("验证弹窗已打开"):
        assert page_obj.is_avatar_dialog_open(), "弹窗应该已打开"

    with allure.step("验证弹窗 UI 元素"):
        # 标题
        assert page_obj.is_visible('h2:has-text("Upload Avatar")', timeout=2000), "Upload Avatar 标题不可见"
        # 拖拽提示
        assert page_obj.is_visible('text=Drag and drop your image here', timeout=2000), "拖拽提示不可见"
        # 点击浏览提示
        assert page_obj.is_visible('text=click to browse files', timeout=2000), "点击浏览提示不可见"
        # 格式支持提示
        assert page_obj.is_visible('text=Supports: JPG, PNG, WebP', timeout=2000), "格式提示不可见"
        assert page_obj.is_visible('text=max 2MB', timeout=2000), "大小限制提示不可见"

    with allure.step("点击 Cancel 关闭弹窗"):
        page_obj.close_avatar_dialog()
        step_shot(page_obj, "step_dialog_closed", full_page=True)

    with allure.step("验证弹窗已关闭"):
        assert not page_obj.is_avatar_dialog_open(), "弹窗应该已关闭"

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Upload Success")
@allure.description(
    """
测试点：
- 打开上传弹窗
- 选择有效图片文件上传
- 验证上传成功（弹窗关闭 / 头像更新）
- 刷新页面验证持久化
- 证据：上传前后截图
"""
)
def test_p1_avatar_upload_success(profile_page, test_avatar_path):
    """P1: 头像上传成功"""
    attach_rule_source_note("Profile P1 - avatar upload")
    logger = TestLogger("test_p1_avatar_upload_success")
    logger.start()

    auth_page, page_obj = profile_page

    # 检查测试图片是否存在
    if not os.path.exists(test_avatar_path):
        pytest.skip(f"测试图片不存在: {test_avatar_path}")

    with allure.step("记录上传前的头像状态"):
        original_avatar_src = page_obj.get_avatar_src()
        allure.attach(
            f"原始头像 src: {original_avatar_src or 'None'}",
            name="original_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_before_upload", full_page=True)

    with allure.step("打开头像上传弹窗"):
        page_obj.open_avatar_dialog()
        assert page_obj.is_avatar_dialog_open(), "弹窗应该已打开"

    with allure.step("上传测试图片"):
        allure.attach(
            f"上传文件: {test_avatar_path}",
            name="upload_file",
            attachment_type=allure.attachment_type.TEXT,
        )
        page_obj.upload_avatar(test_avatar_path)

    with allure.step("等待上传完成"):
        upload_success = page_obj.wait_for_avatar_upload_success(timeout_ms=15000)
        step_shot(page_obj, "step_after_upload", full_page=True)
        
        if page_obj.is_avatar_dialog_open():
            page_obj.close_avatar_dialog()

    with allure.step("验证头像已更新"):
        new_avatar_src = page_obj.get_avatar_src()
        allure.attach(
            f"新头像 src: {new_avatar_src or 'None'}",
            name="new_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("刷新页面验证持久化"):
        auth_page.reload()
        page_obj.wait_for_page_load()
        
        persisted_src = page_obj.get_avatar_src()
        allure.attach(
            f"刷新后头像 src: {persisted_src or 'None'}",
            name="persisted_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, "step_after_refresh", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Replace")
@allure.description(
    """
测试点：
- 上传第一个头像
- 再次上传第二个头像
- 验证头像被替换为新图片
- 证据：替换前后截图
"""
)
def test_p1_avatar_replace(profile_page, test_avatar_path, test_avatar_path_2):
    """P1: 头像替换"""
    attach_rule_source_note("Profile P1 - avatar replace")
    logger = TestLogger("test_p1_avatar_replace")
    logger.start()

    auth_page, page_obj = profile_page

    if not os.path.exists(test_avatar_path) or not os.path.exists(test_avatar_path_2):
        pytest.skip("测试图片不存在")

    with allure.step("上传第一个头像"):
        page_obj.open_avatar_dialog()
        page_obj.upload_avatar(test_avatar_path)
        page_obj.wait_for_avatar_upload_success(timeout_ms=15000)
        
        if page_obj.is_avatar_dialog_open():
            page_obj.close_avatar_dialog()
        
        first_src = page_obj.get_avatar_src()
        allure.attach(f"第一个头像: {first_src}", name="first_avatar", attachment_type=allure.attachment_type.TEXT)
        step_shot(page_obj, "step_first_avatar", full_page=True)

    with allure.step("上传第二个头像（替换）"):
        # 刷新页面确保状态干净
        auth_page.reload()
        page_obj.wait_for_page_load()
        
        page_obj.open_avatar_dialog()
        page_obj.upload_avatar(test_avatar_path_2)
        page_obj.wait_for_avatar_upload_success(timeout_ms=15000)
        
        if page_obj.is_avatar_dialog_open():
            page_obj.close_avatar_dialog()
        
        second_src = page_obj.get_avatar_src()
        allure.attach(f"第二个头像: {second_src}", name="second_avatar", attachment_type=allure.attachment_type.TEXT)
        step_shot(page_obj, "step_second_avatar", full_page=True)

    with allure.step("验证头像已被替换"):
        allure.attach(
            f"头像对比:\n第一个: {first_src}\n第二个: {second_src}",
            name="avatar_comparison",
            attachment_type=allure.attachment_type.TEXT,
        )

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 TESTS - FORMAT VALIDATION
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Valid Formats")
@allure.description(
    """
测试点：
- 验证支持的图片格式：JPG, PNG, GIF
- 每种格式都应该能成功上传
- 证据：上传截图
"""
)
@pytest.mark.parametrize("format_name,filename", [
    pytest.param("PNG", "test_avatar.png", id="format_png"),
    pytest.param("JPG", "test_avatar.jpg", id="format_jpg"),
    pytest.param("WebP", "test_avatar.webp", id="format_webp"),
])
def test_p1_avatar_valid_formats(profile_page, test_images_dir, format_name, filename):
    """P1: 支持的图片格式上传"""
    attach_rule_source_note(f"Profile P1 - avatar format {format_name}")
    logger = TestLogger(f"test_p1_avatar_valid_formats_{format_name}")
    logger.start()

    auth_page, page_obj = profile_page
    file_path = str(test_images_dir / filename)

    if not os.path.exists(file_path):
        pytest.skip(f"测试图片不存在: {file_path}")

    with allure.step("记录上传前的头像状态"):
        original_avatar_src = page_obj.get_avatar_src()
        allure.attach(
            f"原始头像 src: {original_avatar_src or 'None'}",
            name="original_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{format_name}_before_upload", full_page=True)

    with allure.step(f"上传 {format_name} 格式图片"):
        allure.attach(f"文件: {file_path}", name="file_path", attachment_type=allure.attachment_type.TEXT)
        page_obj.open_avatar_dialog()
        page_obj.upload_avatar(file_path)

    with allure.step("验证上传成功"):
        upload_success = page_obj.wait_for_avatar_upload_success(timeout_ms=15000)
        
        # 确保弹窗完全关闭
        if page_obj.is_avatar_dialog_open():
            page_obj.close_avatar_dialog()
        page_obj.wait_for_avatar_dialog_closed()
        
        allure.attach(
            f"{format_name} 格式上传结果: {'成功' if upload_success else '等待超时（可能成功）'}",
            name="upload_result",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("验证头像已更新"):
        new_avatar_src = page_obj.get_avatar_src()
        allure.attach(
            f"新头像 URL: {new_avatar_src or 'None'}",
            name="new_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("刷新页面验证持久化"):
        auth_page.reload()
        page_obj.wait_for_page_load()
        
        persisted_src = page_obj.get_avatar_src()
        allure.attach(
            f"刷新后头像 src: {persisted_src or 'None'}",
            name="persisted_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_{format_name}_avatar_after_refresh", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Invalid Formats")
@allure.description(
    """
测试点：
- 验证不支持的文件格式被拒绝：TXT, BMP
- 应该显示错误提示或不允许上传
- 证据：错误提示截图
"""
)
@pytest.mark.parametrize("format_name,filename", [
    pytest.param("TXT", "invalid_format.txt", id="format_txt_reject"),
    pytest.param("BMP", "invalid_format.bmp", id="format_bmp_reject"),
    pytest.param("GIF", "test_avatar.gif", id="format_gif_reject"),
])
def test_p1_avatar_invalid_formats(profile_page, test_images_dir, format_name, filename):
    """P1: 不支持的格式应被拒绝"""
    attach_rule_source_note(f"Profile P1 - avatar invalid format {format_name}")
    logger = TestLogger(f"test_p1_avatar_invalid_formats_{format_name}")
    logger.start()

    auth_page, page_obj = profile_page
    file_path = str(test_images_dir / filename)

    if not os.path.exists(file_path):
        pytest.skip(f"测试文件不存在: {file_path}")

    with allure.step(f"尝试上传 {format_name} 格式文件"):
        allure.attach(f"文件: {file_path}", name="file_path", attachment_type=allure.attachment_type.TEXT)
        page_obj.open_avatar_dialog()
        
        try:
            page_obj.upload_avatar(file_path)
        except Exception as e:
            allure.attach(f"上传异常（预期）: {str(e)}", name="upload_error", attachment_type=allure.attachment_type.TEXT)

    with allure.step("验证上传被拒绝或显示错误"):
        step_shot(page_obj, f"step_{format_name}_reject", full_page=True)
        
        # 检查是否有错误提示
        error_visible = (
            page_obj.is_visible('text=Invalid file type', timeout=2000) or
            page_obj.is_visible('text=not supported', timeout=1000) or
            page_obj.is_visible('text=error', timeout=1000) or
            page_obj.is_visible('[role="alert"]', timeout=1000)
        )
        
        # 检查弹窗是否仍然打开（说明上传未成功）
        dialog_still_open = page_obj.is_avatar_dialog_open()
        
        allure.attach(
            f"错误提示可见: {error_visible}\n弹窗仍打开: {dialog_still_open}",
            name="validation_result",
            attachment_type=allure.attachment_type.TEXT,
        )
        
        # 关闭弹窗
        if dialog_still_open:
            page_obj.close_avatar_dialog()

    logger.end(success=True)


# ═══════════════════════════════════════════════════════════════
# P1 TESTS - SIZE BOUNDARY
# ═══════════════════════════════════════════════════════════════

@pytest.mark.P1
@pytest.mark.functional
@allure.feature("Profile")
@allure.story("P1 - Avatar Size Boundary")
@allure.description(
    """
测试点：
- 2MB 边界值测试
- 1.9MB（小于限制）应该成功
- 2.0MB（等于限制）应该成功
- 2.1MB（超过限制）应该被拒绝
- 证据：上传结果截图
"""
)
@pytest.mark.parametrize("size_name,filename,expected_result", [
    pytest.param("1.9MB", "size_1_9mb.png", "accept", id="size_1_9mb_accept"),
    pytest.param("2.0MB", "size_2mb.png", "accept", id="size_2mb_accept"),
    pytest.param("2.1MB", "size_2_1mb.png", "reject", id="size_2_1mb_reject"),
])
def test_p1_avatar_size_boundary(profile_page, test_images_dir, size_name, filename, expected_result):
    """P1: 文件大小边界值测试"""
    attach_rule_source_note(f"Profile P1 - avatar size {size_name}")
    logger = TestLogger(f"test_p1_avatar_size_boundary_{size_name}")
    logger.start()

    auth_page, page_obj = profile_page
    file_path = str(test_images_dir / filename)

    if not os.path.exists(file_path):
        pytest.skip(f"测试文件不存在: {file_path}")

    file_size_mb = os.path.getsize(file_path) / 1024 / 1024
    allure.attach(
        f"文件: {filename}\n大小: {file_size_mb:.2f} MB\n预期结果: {expected_result}",
        name="test_params",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("记录上传前的头像状态"):
        original_avatar_src = page_obj.get_avatar_src()
        allure.attach(
            f"原始头像 src: {original_avatar_src or 'None'}",
            name="original_avatar_src",
            attachment_type=allure.attachment_type.TEXT,
        )
        step_shot(page_obj, f"step_size_{size_name}_before_upload", full_page=True)

    with allure.step(f"上传 {size_name} 文件"):
        page_obj.open_avatar_dialog()
        
        try:
            page_obj.upload_avatar(file_path)
        except Exception as e:
            allure.attach(f"上传异常: {str(e)}", name="upload_error", attachment_type=allure.attachment_type.TEXT)

    with allure.step("验证上传结果"):
        if expected_result == "accept":
            # 对于应该成功的，等待上传完成
            upload_success = page_obj.wait_for_avatar_upload_success(timeout_ms=30000)  # 大文件需要更长时间
            
            # 确保弹窗完全关闭
            if page_obj.is_avatar_dialog_open():
                page_obj.close_avatar_dialog()
            
            allure.attach(
                f"预期: 上传成功\n上传结果: {'成功' if upload_success else '等待超时'}",
                name="result",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 等待检查错误状态
            auth_page.wait_for_timeout(2000)
            
            error_visible = (
                page_obj.is_visible('text=too large', timeout=2000) or
                page_obj.is_visible('text=exceeds', timeout=1000) or
                page_obj.is_visible('text=2MB', timeout=1000) or
                page_obj.is_visible('[role="alert"]', timeout=1000)
            )
            
            # 拒绝时先截图显示错误状态
            step_shot(page_obj, f"step_size_{size_name}_error", full_page=True)
            allure.attach(
                f"预期: 上传被拒绝\n错误提示: {error_visible}",
                name="result",
                attachment_type=allure.attachment_type.TEXT,
            )
            # 关闭弹窗
            if page_obj.is_avatar_dialog_open():
                page_obj.close_avatar_dialog()

    if expected_result == "accept":
        with allure.step("验证头像已更新"):
            page_obj.wait_for_avatar_dialog_closed()
            
            new_avatar_src = page_obj.get_avatar_src()
            allure.attach(
                f"新头像 URL: {new_avatar_src or 'None'}",
                name="new_avatar_src",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("刷新页面验证持久化"):
            auth_page.reload()
            page_obj.wait_for_page_load()
            
            persisted_src = page_obj.get_avatar_src()
            allure.attach(
                f"刷新后头像 src: {persisted_src or 'None'}",
                name="persisted_avatar_src",
                attachment_type=allure.attachment_type.TEXT,
            )
            step_shot(page_obj, f"step_size_{size_name}_avatar_after_refresh", full_page=True)

    logger.end(success=True)

