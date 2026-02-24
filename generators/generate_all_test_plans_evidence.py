"""
Generate-all-test-plans evidence and capture helpers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from playwright.sync_api import BrowserContext, Page

from generators.page_analyzer import PageAnalyzer
from generators.test_plan_generator import TestPlanGenerator
from generators.utils import get_file_name_from_url
from utils.logger import get_logger

logger = get_logger(__name__)

_A11Y_CONTROL_ROLES = {
    "button",
    "link",
    "textbox",
    "heading",
    "tab",
    "checkbox",
    "radio",
    "combobox",
    "menuitem",
    "switch",
}


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def try_fetch_json(ctx: BrowserContext, url: str) -> Optional[Dict[str, Any]]:
    try:
        r = ctx.request.get(url)
        if r.ok:
            j = r.json()
            return j if isinstance(j, dict) else None
    except Exception:
        return None
    return None


def extract_password_policy_from_abp_app_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    values = (((cfg.get("settings") or {}).get("values")) or {})
    if not isinstance(values, dict):
        return {}
    keys = [
        "Abp.Identity.Password.RequiredLength",
        "Abp.Identity.Password.RequireDigit",
        "Abp.Identity.Password.RequireLowercase",
        "Abp.Identity.Password.RequireUppercase",
        "Abp.Identity.Password.RequireNonAlphanumeric",
        "Abp.Identity.Password.RequiredUniqueChars",
    ]
    out: Dict[str, Any] = {}
    for k in keys:
        v = values.get(k)
        if isinstance(v, str):
            vv = v.strip().lower()
            if vv in {"true", "false"}:
                out[k] = vv == "true"
                continue
            if vv.isdigit():
                out[k] = int(vv)
                continue
        out[k] = v
    return {k: v for k, v in out.items() if v is not None}


def walk_a11y(node: Any) -> Iterable[Dict[str, str]]:
    if not isinstance(node, dict):
        return []
    out: List[Dict[str, str]] = []
    role = str(node.get("role") or "").strip()
    name = str(node.get("name") or "").strip()
    if role:
        out.append({"role": role, "name": name})
    for ch in (node.get("children") or []):
        out.extend(walk_a11y(ch))
    return out


def escape_for_role_name(v: str) -> str:
    return (v or "").replace('"', '\\"').strip()


def build_locator_hints(controls: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    tabs: Dict[str, str] = {}
    inputs: Dict[str, str] = {}
    buttons: Dict[str, str] = {}
    links: Dict[str, str] = {}

    def keyify(name: str) -> str:
        k = re.sub(r"[^a-zA-Z0-9]+", "_", (name or "").strip().lower()).strip("_")
        return k[:64] or "unnamed"

    for c in controls:
        role = (c.get("role") or "").strip().lower()
        name = (c.get("name") or "").strip()
        if role not in _A11Y_CONTROL_ROLES or not name:
            continue
        loc = f'role={role}[name="{escape_for_role_name(name)}"]'
        k = keyify(name)
        if role == "tab":
            tabs.setdefault(k, loc)
        elif role == "textbox":
            inputs.setdefault(k, loc)
        elif role == "button":
            buttons.setdefault(k, loc)
        elif role == "link":
            links.setdefault(k, loc)
    return {"tabs": tabs, "inputs": inputs, "buttons": buttons, "links": links}


def render_visible_txt(
    *,
    requested_url: str,
    final_url: str,
    title: str,
    login_required_suspect: bool,
    controls: List[Dict[str, str]],
) -> str:
    lines: List[str] = [
        f"url: {requested_url}",
        f"final_url: {final_url}",
        f"title: {title}",
        f"login_required_suspect: {str(bool(login_required_suspect)).lower()}",
        "",
        "controls:",
    ]
    seen: Set[Tuple[str, str]] = set()
    for c in controls:
        role = (c.get("role") or "").strip()
        name = (c.get("name") or "").strip()
        if not role or role.lower() not in _A11Y_CONTROL_ROLES:
            continue
        key = (role, name)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"  - {role}: {name}" if name else f"  - {role}:")
    if len(seen) == 0:
        lines.append("  - (no_controls_detected)")
    lines.append("")
    return "\n".join(lines)


def capture_and_generate_one(
    *,
    page: Page,
    url: str,
    is_same_origin_fn,
    is_login_like_fn,
    docs_root: Path,
    abp_app_cfg: Optional[Dict[str, Any]],
    backend_swagger: Optional[Dict[str, Any]],
    abp_swagger: Optional[Dict[str, Any]],
    auth_required: bool,
) -> str:
    slug = get_file_name_from_url(url)
    artifacts_dir = docs_root / "test-plans" / "artifacts" / slug
    ensure_dir(artifacts_dir)

    requested_url = url
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(800)
    except Exception:
        write_json(
            artifacts_dir / "metadata.json",
            {
                "slug": slug,
                "url": requested_url,
                "title": "",
                "auth_required": auth_required,
                "evidence_files": ["metadata.json"],
                "error": "goto_failed",
            },
        )
        return slug

    final_url = page.url or requested_url
    try:
        title = page.title() or ""
    except Exception:
        title = ""

    try:
        snap = page.accessibility.snapshot()
        flat = list(walk_a11y(snap))
        controls = [{"role": x.get("role") or "", "name": x.get("name") or ""} for x in flat if isinstance(x, dict)]
    except Exception:
        controls = []

    redirected_off_origin = bool(final_url) and not is_same_origin_fn(final_url)
    login_required_suspect = redirected_off_origin or (is_login_like_fn(final_url) and not is_login_like_fn(requested_url))
    locator_hints = build_locator_hints(controls)

    try:
        (artifacts_dir / "visible.html").write_text(page.content() or "", encoding="utf-8")
    except Exception:
        (artifacts_dir / "visible.html").write_text("", encoding="utf-8")
    try:
        page.screenshot(path=str(artifacts_dir / "page.png"), full_page=True)
    except Exception:
        pass
    (artifacts_dir / "visible.txt").write_text(
        render_visible_txt(
            requested_url=requested_url,
            final_url=final_url,
            title=title,
            login_required_suspect=login_required_suspect,
            controls=controls,
        ),
        encoding="utf-8",
    )

    notes: List[str] = []
    pwd_policy: Dict[str, Any] = {}
    if abp_app_cfg:
        try:
            write_json(artifacts_dir / "abp_app_config.json", abp_app_cfg)
            pwd_policy = extract_password_policy_from_abp_app_config(abp_app_cfg)
        except Exception:
            notes.append("abp_app_config_write_failed")
    else:
        notes.append("abp_app_config_unavailable")
    if backend_swagger:
        try:
            write_json(artifacts_dir / "backend_swagger.json", backend_swagger)
        except Exception:
            notes.append("backend_swagger_write_failed")
    else:
        notes.append("backend_swagger_unavailable")
    if abp_swagger:
        try:
            write_json(artifacts_dir / "abp_swagger.json", abp_swagger)
        except Exception:
            notes.append("abp_swagger_write_failed")
    else:
        notes.append("abp_swagger_unavailable")

    try:
        write_json(
            artifacts_dir / "abp_rules_extract.json",
            {
                "source": {
                    "abp_app_config": "abp_app_config.json",
                    "backend_swagger": "backend_swagger.json",
                    "abp_swagger": "abp_swagger.json",
                },
                "password_policy": pwd_policy,
                "notes": notes,
                "api_contract": {
                    "method": "TBD",
                    "path": "TBD",
                    "tag": "TBD",
                    "request_schema": "TBD",
                    "request_constraints": {},
                    "responses": {},
                    "error_schema": "TBD",
                    "error_shape": {},
                },
            },
        )
    except Exception:
        pass

    evidence_candidates = [
        "visible.html",
        "visible.txt",
        "page.png",
        "metadata.json",
        "abp_app_config.json",
        "backend_swagger.json",
        "abp_swagger.json",
        "abp_rules_extract.json",
    ]
    evidence_files = [x for x in evidence_candidates if (artifacts_dir / x).exists()]
    write_json(
        artifacts_dir / "metadata.json",
        {
            "slug": slug,
            "url": requested_url,
            "final_url": final_url,
            "title": title,
            "auth_required": auth_required,
            "evidence_files": evidence_files,
            "locator_hints": locator_hints,
        },
    )

    analyzer = PageAnalyzer()
    try:
        page_info = analyzer._analyze_page(page, requested_url)  # noqa: SLF001
        page_info.auth_required = auth_required
    except Exception:
        from generators.page_types import PageInfo

        page_info = PageInfo(url=requested_url, title=title, page_type="FORM", auth_required=auth_required)

    md = TestPlanGenerator().generate(page_info)
    plan_path = docs_root / "test-plans" / f"{slug}.md"
    plan_path.write_text(md, encoding="utf-8")
    return slug
