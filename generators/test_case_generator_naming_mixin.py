"""
TestCaseGenerator naming/domain helpers.
"""

from __future__ import annotations

from typing import List, Tuple

from generators.page_types import PageInfo
from generators.utils import get_page_name_from_url


class TestCaseGeneratorNamingMixin:
    def _infer_module_and_page(self, segments: List[str]) -> Tuple[str, str]:
        if not segments:
            return "root", "home"
        if len(segments) == 1:
            return segments[0], segments[0]
        module = segments[0]
        page_parts = segments[1:]
        safe_parts = [(p or "").replace("-", "_") for p in page_parts if p]
        page = "_".join(safe_parts) if safe_parts else segments[1]
        return module, page

    def _infer_page_key(self, page: str, page_type: str) -> str:
        return f"{page}_settings" if page_type == "SETTINGS" else page

    def _is_change_password_page(self, *, url_path: str, page_info: PageInfo) -> bool:
        p = (url_path or "").lower()
        if "change-password" in p or "change_password" in p:
            return True
        name = (get_page_name_from_url(page_info.url) or "").lower()
        return "changepassword" in name or "change_password" in name
