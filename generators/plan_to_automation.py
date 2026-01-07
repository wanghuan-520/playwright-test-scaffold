"""
# ═══════════════════════════════════════════════════════════════
# Step2: Plan -> Automation Code Generator
# ═══════════════════════════════════════════════════════════════
#
# 输入：
# - docs/test-plans/<slug>.md
# - docs/test-plans/artifacts/<slug>/metadata.json（优先：locator_hints/auth_required）
#
# 输出（对齐 .cursor/rules/ui-automation-code-generator.mdc）：
# - pages/<slug>_page.py
# - tests/<module>/<domain>/<page>/test_*_{p0,p1,p2,security}.py
# - test-data/<slug>_data.json
#
# 注意：
# - 默认不覆盖已存在文件（避免把手写 suite 覆盖掉）。
# - 密码字段只能通过 PageActions.secret_fill 处理（生成器已在 PageObjectGenerator 里保证）。
#
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from generators.page_types import PageInfo, PageElement
from generators.test_code_generator import TestCodeGenerator
from utils.logger import get_logger

logger = get_logger(__name__)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _slug_from_plan_path(p: Path) -> str:
    return p.stem.strip()


def _parse_plan_core(md_text: str) -> Tuple[str, str, Optional[bool]]:
    """
    从 plan markdown 中提取：
    - url
    - page_type
    - auth_required（是/否）
    """
    url = ""
    page_type = "FORM"
    auth_required: Optional[bool] = None

    m_url = re.search(r"\*\*URL\*\*:\s*`([^`]+)`", md_text)
    if m_url:
        url = (m_url.group(1) or "").strip()

    m_type = re.search(r"\*\*页面类型\*\*:\s*([A-Z_]+)", md_text)
    if m_type:
        page_type = (m_type.group(1) or "").strip() or "FORM"

    m_auth = re.search(r"\*\*是否需要登录态\*\*:\s*(是|否)", md_text)
    if m_auth:
        auth_required = True if m_auth.group(1) == "是" else False

    return url, page_type, auth_required


def _load_metadata(artifacts_dir: Path) -> Dict[str, Any]:
    p = artifacts_dir / "metadata.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="ignore") or "{}")
    except Exception:
        return {}


def _elements_from_locator_hints(locator_hints: Dict[str, Any]) -> List[PageElement]:
    """
    将 Step1 metadata.json 的 locator_hints 转成 PageElement 列表。
    """
    elems: List[PageElement] = []
    if not isinstance(locator_hints, dict):
        return elems

    def _add(kind: str, name: str, selector: str) -> None:
        n = (name or "").strip()
        sel = (selector or "").strip()
        if not sel:
            return
        input_type = ""
        if kind == "inputs":
            key = (n + " " + sel).lower()
            input_type = "password" if "password" in key else "text"
        elems.append(
            PageElement(
                selector=sel,
                tag="",
                type=("input" if kind == "inputs" else ("button" if kind in {"buttons", "tabs"} else "link")),
                text=n,
                placeholder=n,
                name=n,
                id="",
                role="",
                required=False,
                disabled=False,
                attributes={"type": input_type} if input_type else {},
            )
        )

    for sec in ["tabs", "inputs", "buttons", "links"]:
        d = locator_hints.get(sec)
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            _add(sec, str(k), str(v))

    # 去重（按 selector）
    seen = set()
    uniq: List[PageElement] = []
    for e in elems:
        s = (e.selector or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        uniq.append(e)
    return uniq


def _should_skip_existing(path: Path, overwrite: bool) -> bool:
    return (path.exists() and not overwrite)

def _infer_suite_dir_from_url(url: str) -> Path:
    """
    与 generators/test_case_generator.py 当前实现对齐的“套件目录”推导（用于避免覆盖手写 suite）。
    """
    path = (urlparse(url).path or "/").strip("/")
    segs = [s for s in path.split("/") if s]
    if not segs:
        return Path("tests") / "root" / "home"
    if len(segs) == 1:
        return Path("tests") / segs[0] / segs[0]
    # 与 TestCaseGenerator._infer_module_and_page 一致：module=seg0, page="_".join(seg1..)
    module = segs[0]
    safe_parts = [(p or "").replace("-", "_") for p in segs[1:] if p]
    page = "_".join(safe_parts) if safe_parts else segs[1]
    return Path("tests") / module / page

def _suite_exists(url: str, *, root: Path) -> bool:
    suite_dir = (root / _infer_suite_dir_from_url(url)).resolve()
    if not suite_dir.exists():
        return False
    # 任意 test 文件/辅助文件存在都视为“已有套件”
    try:
        if any(suite_dir.glob("test_*.py")):
            return True
        if (suite_dir / "_helpers.py").exists():
            return True
    except Exception:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--plans-dir",
        default="docs/test-plans",
        help="测试计划目录（包含 <slug>.md 与 artifacts/）",
    )
    ap.add_argument(
        "--slug",
        default="",
        help="只处理指定 slug（对应 docs/test-plans/<slug>.md），为空则处理全部",
    )
    ap.add_argument("--overwrite", action="store_true", default=False, help="覆盖已存在 files（默认不覆盖）")
    args = ap.parse_args()

    root = _project_root()
    plans_dir = Path(args.plans_dir)
    if not plans_dir.is_absolute():
        plans_dir = (root / plans_dir).resolve()

    artifacts_root = plans_dir / "artifacts"
    if not plans_dir.exists():
        raise SystemExit(f"plans_dir not found: {plans_dir}")

    gen = TestCodeGenerator()
    count = 0

    for plan_path in sorted(plans_dir.glob("*.md")):
        if plan_path.name.startswith("_"):
            continue
        if (args.slug or "").strip() and plan_path.stem.strip() != (args.slug or "").strip():
            continue
        slug = _slug_from_plan_path(plan_path)
        md = plan_path.read_text(encoding="utf-8", errors="ignore") or ""
        url, page_type, auth_required_from_plan = _parse_plan_core(md)
        if not url:
            logger.warning(f"skip plan (missing URL): {plan_path}")
            continue

        art_dir = artifacts_root / slug
        meta = _load_metadata(art_dir)
        locator_hints = (meta.get("locator_hints") or {}) if isinstance(meta, dict) else {}

        elements = _elements_from_locator_hints(locator_hints)
        auth_required = meta.get("auth_required") if isinstance(meta.get("auth_required"), bool) else auth_required_from_plan

        page_info = PageInfo(
            url=url,
            title=str(meta.get("title") or ""),
            page_type=page_type,
            auth_required=auth_required if isinstance(auth_required, bool) else None,
            elements=elements,
            forms=[],
            navigation=[],
        )

        # 预判关键输出路径是否存在：默认不覆盖
        file_name = slug
        page_py = root / "pages" / f"{file_name}_page.py"
        data_json = root / "test-data" / f"{file_name}_data.json"
        # tests 目录由 TestCaseGenerator 推导；为了避免覆盖手写 suite：
        # - 未开启 overwrite 时，只要 suite 已存在，就跳过该计划
        if (not args.overwrite) and _suite_exists(url, root=root):
            logger.info(f"skip (suite exists): {slug}")
            continue
        if _should_skip_existing(page_py, args.overwrite) and _should_skip_existing(data_json, args.overwrite):
            logger.info(f"skip (exists): {slug}")
            continue

        # 生成并落盘
        logger.info(f"generate: {slug} url={url}")
        gen.generate_all(page_info, output_dir=str(root))
        count += 1

    logger.info(f"done: generated {count} plans into pages/tests/test-data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


