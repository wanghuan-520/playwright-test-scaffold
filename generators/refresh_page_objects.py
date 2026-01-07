"""
刷新生成：仅重写 pages/<slug>_page.py（不改 tests/），用于修复生成器模板升级后的语法/安全问题。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from generators.page_object_generator import PageObjectGenerator
from generators.page_types import PageInfo, PageElement
from utils.logger import get_logger

logger = get_logger(__name__)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _slug_from_plan_path(p: Path) -> str:
    return p.stem.strip()


def _parse_plan_core(md_text: str) -> Tuple[str, str, Optional[bool]]:
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

    seen = set()
    uniq: List[PageElement] = []
    for e in elems:
        s = (e.selector or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        uniq.append(e)
    return uniq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans-dir", default="docs/test-plans")
    ap.add_argument("--slug", default="", help="只刷新指定 slug 的 page object（为空则刷新全部）")
    args = ap.parse_args()

    root = _project_root()
    plans_dir = Path(args.plans_dir)
    if not plans_dir.is_absolute():
        plans_dir = (root / plans_dir).resolve()
    artifacts_root = plans_dir / "artifacts"

    pog = PageObjectGenerator()

    for plan_path in sorted(plans_dir.glob("*.md")):
        if plan_path.name.startswith("_"):
            continue
        if (args.slug or "").strip() and plan_path.stem.strip() != (args.slug or "").strip():
            continue
        slug = _slug_from_plan_path(plan_path)
        md = plan_path.read_text(encoding="utf-8", errors="ignore") or ""
        url, page_type, auth_required_from_plan = _parse_plan_core(md)
        if not url:
            continue
        meta = _load_metadata(artifacts_root / slug)
        elems = _elements_from_locator_hints(meta.get("locator_hints") or {})
        auth_required = meta.get("auth_required") if isinstance(meta.get("auth_required"), bool) else auth_required_from_plan

        page_info = PageInfo(
            url=url,
            title=str(meta.get("title") or ""),
            page_type=page_type,
            auth_required=auth_required if isinstance(auth_required, bool) else None,
            elements=elems,
            forms=[],
            navigation=[],
        )

        out = root / "pages" / f"{slug}_page.py"
        code = pog.generate_page_object(page_info)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(code, encoding="utf-8")
        logger.info(f"refreshed page object: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


