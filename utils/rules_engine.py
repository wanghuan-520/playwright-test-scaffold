"""
# ═══════════════════════════════════════════════════════════════
# Rules Engine (Structured, Executable)
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 把 docs/rules.yaml 变成“可执行规则源”（生成/执行过程真正读取并据此决策）
# - 默认值与当前行为保持一致：rules.yaml 缺失时也能跑
#
# 约束：
# - 不强依赖第三方：优先用 PyYAML；缺失时用内置 YAML 子集解析器兜底
# - 文件短小、可读、可测试
#
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Config model (minimal)
# ═══════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RulesConfig:
    # flow.runtime_rules_context
    runtime_rules_context_enabled: bool = True
    runtime_rules_context_output_path: str = "reports/rules_context.md"

    # analysis.default_storage_state
    default_storage_state_enabled: bool = True
    default_storage_state_prefer: str = ".auth/storage_state.master.json"
    default_storage_state_fallback_glob: str = ".auth/storage_state.*.json"

    # pytest.default_target_from_url
    pytest_default_target_from_url_enabled: bool = True

    # generation.suite_files
    suite_files: Tuple[str, ...] = ("p0", "p1", "p2", "security")

    # plan.output_path
    plan_output_path: str = ""

    # page_object.loaded_indicator
    page_loaded_indicator_settings: str = "save_button"
    page_loaded_indicator_default: str = "first_input"


# ═══════════════════════════════════════════════════════════════
# Loader (yaml or fallback)
# ═══════════════════════════════════════════════════════════════


_CACHE: Dict[str, Any] = {"key": None, "cfg": None}


def rules_config_path(root: Optional[Path] = None) -> Path:
    r = root or Path(__file__).resolve().parent.parent
    env = (os.getenv("PT_RULES_CONFIG_PATH") or "").strip()
    if env:
        return Path(env).expanduser()
    return r / "docs" / "rules.yaml"


def get_rules_config(*, root: Optional[Path] = None, force_reload: bool = False) -> RulesConfig:
    """
    读取 docs/rules.yaml，返回结构化 RulesConfig（带默认值）。
    """
    r = root or Path(__file__).resolve().parent.parent
    p = rules_config_path(r)
    cache_key = f"{p.resolve()}"
    if (not force_reload) and _CACHE.get("key") == cache_key and _CACHE.get("cfg") is not None:
        return _CACHE["cfg"]

    raw = _load_yaml_like(p)
    cfg = _coerce_rules_config(raw)
    _CACHE["key"] = cache_key
    _CACHE["cfg"] = cfg
    return cfg


def _load_yaml_like(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}

    text = path.read_text(encoding="utf-8", errors="ignore")

    # Prefer PyYAML
    try:
        import yaml  # type: ignore

        obj = yaml.safe_load(text)  # noqa: S506
        return obj if isinstance(obj, dict) else {}
    except Exception:
        # Fallback: minimal YAML subset parser (dict + list of scalars + strings/bools/ints)
        return _parse_yaml_subset(text)


def _parse_yaml_subset(text: str) -> Dict[str, Any]:
    """
    解析 YAML 子集：
    - key: value
    - key:
      nested: value
    - list:
      - a
      - b
    备注：只支持空格缩进（2+），忽略注释行与空行。
    """
    root: Dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(0, root)]  # (indent, container)

    def parse_scalar(v: str) -> Any:
        s = v.strip()
        if not s:
            return ""
        if s.lower() in {"true", "false"}:
            return s.lower() == "true"
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        try:
            return int(s)
        except Exception:
            return s

    lines = text.splitlines()
    for ln in lines:
        raw = ln.rstrip("\n")
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))

        # find parent container by indent
        while stack and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root

        # list item
        if s.startswith("- "):
            item = parse_scalar(s[2:])
            if not isinstance(parent, list):
                # create a list in parent is impossible without knowing key; ignore
                continue
            parent.append(item)
            continue

        # key: value / key:
        if ":" not in s:
            continue
        key, rest = s.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        if rest == "":
            # create dict by default; if next lines are list items, caller must pre-create list
            # Here we create dict; if later we see list items, we will switch to list when detected.
            container: Any = {}
            if isinstance(parent, dict):
                parent[key] = container
                stack.append((indent + 2, container))
            continue

        value = parse_scalar(rest)
        if isinstance(parent, dict):
            parent[key] = value
            # If value is to be a list, user must provide "- ..." under it; we can auto-upgrade when needed,
            # but keep minimal for now.

    # Second pass: upgrade dict placeholders to list when YAML used "key:" then "- item" (not supported fully here).
    # For our current docs/rules.yaml, PyYAML should be available; fallback is best-effort.
    return root


def _dig(d: Dict[str, Any], path: str, default: Any) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
        if cur is None:
            return default
    return cur


def _coerce_rules_config(raw: Dict[str, Any]) -> RulesConfig:
    # Disabled engine => return defaults
    enabled = bool(_dig(raw, "rules_engine.enabled", True))
    if not enabled:
        return RulesConfig(
            runtime_rules_context_enabled=False,
            default_storage_state_enabled=False,
            pytest_default_target_from_url_enabled=False,
        )

    suite_files = _dig(raw, "generation.suite_files", None)
    if isinstance(suite_files, list):
        suite_files_t = tuple(str(x).strip() for x in suite_files if str(x).strip())
    else:
        suite_files_t = RulesConfig().suite_files

    # ═══════════════════════════════════════════════════════════════
    # Runtime override (plan-driven)
    # - PT_SUITE_FILES="p0,p2,security"
    # ═══════════════════════════════════════════════════════════════
    env_suite = (os.getenv("PT_SUITE_FILES") or "").strip()
    if env_suite:
        parts = [p.strip().lower() for p in env_suite.split(",") if p.strip()]
        parts = [p for p in parts if p in {"p0", "p1", "p2", "security"}]
        if parts:
            suite_files_t = tuple(parts)

    return RulesConfig(
        runtime_rules_context_enabled=bool(_dig(raw, "flow.runtime_rules_context.enabled", True)),
        runtime_rules_context_output_path=str(_dig(raw, "flow.runtime_rules_context.output_path", "reports/rules_context.md")),
        default_storage_state_enabled=bool(_dig(raw, "analysis.default_storage_state.enabled", True)),
        default_storage_state_prefer=str(_dig(raw, "analysis.default_storage_state.prefer", ".auth/storage_state.master.json")),
        default_storage_state_fallback_glob=str(_dig(raw, "analysis.default_storage_state.fallback_glob", ".auth/storage_state.*.json")),
        pytest_default_target_from_url_enabled=bool(_dig(raw, "pytest.default_target_from_url.enabled", True)),
        suite_files=suite_files_t or RulesConfig().suite_files,
        plan_output_path=str(_dig(raw, "plan.output_path", "")),
        page_loaded_indicator_settings=str(_dig(raw, "page_object.loaded_indicator.settings", "save_button")),
        page_loaded_indicator_default=str(_dig(raw, "page_object.loaded_indicator.default", "first_input")),
    )


