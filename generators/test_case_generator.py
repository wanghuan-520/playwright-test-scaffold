# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Case Generator
# ═══════════════════════════════════════════════════════════════
"""
测试用例生成器（协调器）。

保持原接口：
- `generate_test_suite(page_info) -> Dict[str, str]`
- `generate_test_cases(page_info) -> str`（兼容提示）
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from generators.page_types import PageInfo
from generators.rule_deriver import RuleDeriver
from generators.test_case_generator_helpers_mixin import TestCaseGeneratorHelpersMixin
from generators.test_case_generator_naming_mixin import TestCaseGeneratorNamingMixin
from generators.test_case_generator_p0_mixin import TestCaseGeneratorP0Mixin
from generators.test_case_generator_p1_mixin import TestCaseGeneratorP1Mixin
from generators.test_case_generator_p2_security_mixin import TestCaseGeneratorP2SecurityMixin
from generators.utils import extract_url_path
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerator(
    TestCaseGeneratorNamingMixin,
    TestCaseGeneratorHelpersMixin,
    TestCaseGeneratorP0Mixin,
    TestCaseGeneratorP1Mixin,
    TestCaseGeneratorP2SecurityMixin,
):
    """生成测试用例（多文件套件）。"""

    def generate_test_suite(self, page_info: PageInfo) -> Optional[Dict[str, str]]:
        enabled = {"p0", "p1", "p2", "security"}
        try:
            from utils.rules_engine import get_rules_config

            cfg_rules = get_rules_config()
            enabled = {str(x).strip().lower() for x in (cfg_rules.suite_files or ()) if str(x).strip()}
            enabled = enabled & {"p0", "p1", "p2", "security"} if enabled else {"p0", "p1", "p2", "security"}
        except Exception:
            pass

        url_path = extract_url_path(page_info.url)
        segments = [s for s in url_path.strip("/").split("/") if s]
        module, page = self._infer_module_and_page(segments)
        base_dir = f"tests/{module}/{page}"
        page_key = self._infer_page_key(page, page_info.page_type)
        is_change_password = self._is_change_password_page(url_path=url_path, page_info=page_info)

        cfg = ConfigManager()
        deriver = RuleDeriver.from_config(cfg)
        rules = deriver.derive(page_info)

        def _exists(p: str) -> bool:
            try:
                return bool(p) and Path(str(p)).expanduser().exists()
            except Exception:
                return False

        has_static_repo = _exists(cfg.get("repositories.frontend.local_path", "")) or _exists(
            cfg.get("repositories.backend.local_path", "")
        )
        if has_static_repo and not rules:
            raise RuntimeError(
                "Static rule derivation failed (repositories.*.local_path provided but no rules derived). "
                "Refusing to guess. Please fix repo path or parsing logic."
            )

        suite: Dict[str, str] = {
            f"tests/{module}/__init__.py": "",
            f"{base_dir}/__init__.py": "",
            f"{base_dir}/_helpers.py": self._helpers_py(page_info, rules, is_change_password=is_change_password),
        }
        if "p0" in enabled:
            suite[f"{base_dir}/test_{page_key}_p0.py"] = self._p0_py(
                page_info, module, page, page_key, rules, is_change_password=is_change_password
            )
        if "p1" in enabled:
            suite[f"{base_dir}/test_{page_key}_p1.py"] = self._p1_py(
                page_info, module, page, page_key, rules, is_change_password=is_change_password
            )
        if "p2" in enabled:
            suite[f"{base_dir}/test_{page_key}_p2.py"] = self._p2_py(page_info, module, page, page_key, rules)
        if "security" in enabled:
            suite[f"{base_dir}/test_{page_key}_security.py"] = self._security_py(page_info, module, page, page_key, rules)

        return suite

    def generate_test_cases(self, page_info: PageInfo) -> str:
        suite = self.generate_test_suite(page_info)
        if not suite:
            raise RuntimeError("suite generation disabled")
        return (
            "# This project generates a multi-file test suite by default.\n"
            "# Use TestCodeGenerator.generate_all(page_info) to write files to disk.\n"
        )
