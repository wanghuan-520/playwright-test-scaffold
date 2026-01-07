import allure
import pytest
from playwright.sync_api import Page

from utils.config import ConfigManager


def _backend_base() -> str:
    """
    管理类 API 在 BusinessServer HttpApi.Host（默认 44345）。
    """
    backend = (ConfigManager().get_service_url("backend") or "").rstrip("/")
    if backend.endswith(":44320"):
        return backend[:-6] + ":44345"
    return backend


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AdminSettingsFeatureManagement")
@allure.story("P1 - ABP Constraints")
@allure.title("Feature list：鉴权/返回结构（200 或 403）")
def test_p1_feature_list_requires_auth_and_has_shape(auth_page: Page):
    page = auth_page
    base = _backend_base()

    resp = page.request.get(f"{base}/api/feature-management/features")
    assert resp.status in {200, 401, 403}, f"expected 200/401/403 but got {resp.status}"
    if resp.status == 200:
        data = resp.json()
        assert "groups" in data, "expected GetFeatureListResultDto.groups"
    elif resp.status == 401:
        pytest.skip("unauthorized session for feature list (401)")


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("AdminSettingsFeatureManagement")
@allure.story("P1 - ABP Constraints")
@allure.title("Feature update：非法 body 应 400（若无权限则 403）")
def test_p1_feature_update_invalid_body_should_reject_or_forbid(auth_page: Page):
    page = auth_page
    base = _backend_base()

    # invalid shape: UpdateFeaturesDto expects { features: [...] }
    resp = page.request.put(f"{base}/api/feature-management/features", data={"oops": 1})
    assert resp.status in {400, 401, 403}, f"expected 400/401/403 but got {resp.status}"
    if resp.status == 401:
        pytest.skip("unauthorized session for feature update (401)")


