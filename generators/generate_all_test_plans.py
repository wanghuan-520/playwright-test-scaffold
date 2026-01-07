"""
# ═══════════════════════════════════════════════════════════════
# Generate UI Test Plans for All Pages (Crawler)
# ═══════════════════════════════════════════════════════════════
#
# 目标：
# - 基于 `.cursor/rules/ui-test-plan-generator.mdc` 的 Step1 规则，
#   对指定 base_url 下“可达页面”生成测试计划与证据链：
#   - docs/test-plans/<slug>.md
#   - docs/test-plans/artifacts/<slug>/{visible.html,visible.txt,page.png,metadata.json}
#
# 约束（必须）：
# - 不把密码写进计划或任何落盘文件
# - 不落盘 token/cookie/storageState（本脚本不调用 storage_state(path=...)）
# - 环境真理源：config/project.yaml（由 ConfigManager 读取）
#
# 说明：
# - “所有页面”采用可执行口径：对同源 URL 做 BFS（从 / 开始），收集 <a href> 的路由。
# - 权限分层：匿名 + 已登录（账号池）。若项目确实区分 admin 权限，可再扩展第三类凭证。
#
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import sync_playwright, Page, BrowserContext

from generators.page_analyzer import PageAnalyzer
from generators.test_plan_generator import TestPlanGenerator
from generators.utils import get_file_name_from_url
from pages.login_page import LoginPage
from utils.config import ConfigManager
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# URL helpers
# ═══════════════════════════════════════════════════════════════

_ASSET_EXTS = {
    ".js",
    ".css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".zip",
}


def _canonicalize(url: str) -> str:
    """
    归一化 URL（同源爬站用）：
    - 去掉 fragment/query
    - path 去掉多余的末尾 /
    """
    p = urlparse(url)
    path = p.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((p.scheme, p.netloc, path, "", "", ""))


def _is_same_origin(url: str, origin: str) -> bool:
    u = urlparse(url)
    o = urlparse(origin)
    return (u.scheme, u.netloc) == (o.scheme, o.netloc)

def _origin_of(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _is_probably_asset(url: str) -> bool:
    p = urlparse(url)
    path = (p.path or "").lower()
    if not path:
        return False
    if path.startswith("/_next/") or path.startswith("/static/") or path.startswith("/assets/"):
        return True
    for ext in _ASSET_EXTS:
        if path.endswith(ext):
            return True
    return False


def _is_login_like(url: str) -> bool:
    """
    识别“登录页/认证跳转页”：
    - ABP 常见：/Account/Login
    - 前端常见：/auth/login
    """
    path = (urlparse(url).path or "").lower()
    return any(x in path for x in ["/account/login", "/auth/login", "/login", "/signin"])


def _extract_links(page: Page, *, origin: str) -> List[str]:
    """
    从当前页面抽取同源链接（只抽 <a href>，避免误触按钮/脚本）。
    """
    hrefs: List[str] = []
    try:
        locs = page.locator("a[href]").all()
    except Exception:
        locs = []
    for loc in locs:
        try:
            href = (loc.get_attribute("href") or "").strip()
        except Exception:
            href = ""
        if not href:
            continue
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue

        abs_url = _canonicalize(urljoin(origin, href))
        if not abs_url.startswith("http"):
            continue
        if not _is_same_origin(abs_url, origin):
            continue
        if _is_probably_asset(abs_url):
            continue
        hrefs.append(abs_url)
    return hrefs


# ═══════════════════════════════════════════════════════════════
# Evidence: visible txt/html + metadata
# ═══════════════════════════════════════════════════════════════

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


def _walk_a11y(node: Any) -> Iterable[Dict[str, str]]:
    """
    扁平化 a11y snapshot，提取 role/name（用于 visible.txt）
    """
    if not isinstance(node, dict):
        return []
    out: List[Dict[str, str]] = []
    role = str(node.get("role") or "").strip()
    name = str(node.get("name") or "").strip()
    if role:
        out.append({"role": role, "name": name})
    for ch in (node.get("children") or []):
        out.extend(_walk_a11y(ch))
    return out


def _escape_for_role_name(v: str) -> str:
    return (v or "").replace('"', '\\"').strip()


def _build_locator_hints(controls: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    生成 role-based locator hints（metadata.json 用）。
    """
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
        if role not in _A11Y_CONTROL_ROLES:
            continue
        if not name:
            continue
        loc = f'role={role}[name="{_escape_for_role_name(name)}"]'
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


def _render_visible_txt(
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

    # 保持可读性：只输出“可交互/可观测”的 role
    seen: Set[Tuple[str, str]] = set()
    for c in controls:
        role = (c.get("role") or "").strip()
        name = (c.get("name") or "").strip()
        if not role:
            continue
        if role.lower() not in _A11Y_CONTROL_ROLES:
            continue
        key = (role, name)
        if key in seen:
            continue
        seen.add(key)
        if name:
            lines.append(f"  - {role}: {name}")
        else:
            lines.append(f"  - {role}:")
    if len(seen) == 0:
        lines.append("  - (no_controls_detected)")
    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# ABP rule snapshots (global -> per page copy)
# ═══════════════════════════════════════════════════════════════


def _try_fetch_json(ctx: BrowserContext, url: str) -> Optional[Dict[str, Any]]:
    try:
        r = ctx.request.get(url)
        if r.ok:
            j = r.json()
            return j if isinstance(j, dict) else None
    except Exception:
        return None
    return None


def _extract_password_policy_from_abp_app_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
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
        # 尽量转类型：数字/布尔
        if isinstance(v, str):
            vv = v.strip().lower()
            if vv in {"true", "false"}:
                out[k] = vv == "true"
                continue
            if vv.isdigit():
                out[k] = int(vv)
                continue
        out[k] = v
    # 清理 None
    return {k: v for k, v in out.items() if v is not None}


# ═══════════════════════════════════════════════════════════════
# Crawl & generate
# ═══════════════════════════════════════════════════════════════


def _crawl_urls(
    page: Page,
    *,
    origin: str,
    start_url: str,
    max_pages: int,
) -> Tuple[Set[str], Set[str]]:
    """
    BFS 爬站收集同源页面 URL（不写任何落盘）
    """
    q: List[str] = [_canonicalize(start_url)]
    seen: Set[str] = set()
    accessible: Set[str] = set()

    while q and len(seen) < max_pages:
        url = q.pop(0)
        if url in seen:
            continue
        seen.add(url)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(500)
        except Exception:
            continue

        # 能否匿名访问（避免“被跳到登录页”但误判为可访问）
        final_url = ""
        try:
            final_url = page.url or ""
        except Exception:
            final_url = ""
        redirected_off_origin = bool(final_url) and not _is_same_origin(final_url, origin)
        login_redirect = redirected_off_origin or (_is_login_like(final_url) and not _is_login_like(url))
        if not login_redirect:
            accessible.add(url)

        # 如果被跳到登录页，也把链接继续抽（允许发现注册/忘记密码等）
        for u in _extract_links(page, origin=origin):
            if u not in seen:
                q.append(u)

    return seen, accessible


def _login_with_account_pool(page: Page) -> Dict[str, str]:
    """
    使用账号池登录（不落盘 storageState）。
    返回：账号信息（仅用于日志，避免写入 artifacts）。
    """
    # 允许用户在本机通过环境变量提供登录凭证（避免把密码写进命令行/文档/代码）。
    # - PT_LOGIN_EMAIL
    # - PT_LOGIN_PASSWORD
    import os

    env_email = (os.getenv("PT_LOGIN_EMAIL") or "").strip()
    env_pwd = os.getenv("PT_LOGIN_PASSWORD") or ""
    if env_email and env_pwd:
        LoginPage(page).login(username=env_email, password=env_pwd)
        return {"username": env_email, "email": env_email, "source": "env"}

    dm = DataManager()
    acc = dm.get_test_account("__generate_test_plans__")
    username = acc.get("email") or acc.get("username") or ""
    password = acc.get("password") or ""
    if not username or not password:
        raise RuntimeError("账号池未提供可用凭证（email/password 为空）")

    LoginPage(page).login(username=username, password=password)
    return {"username": str(acc.get("username") or ""), "email": str(acc.get("email") or ""), "source": "account_pool"}


def _capture_and_generate_one(
    *,
    page: Page,
    url: str,
    origin: str,
    docs_root: Path,
    abp_app_cfg: Optional[Dict[str, Any]],
    backend_swagger: Optional[Dict[str, Any]],
    abp_swagger: Optional[Dict[str, Any]],
    auth_required: bool,
) -> str:
    """
    打开页面并生成：
    - artifacts/<slug>/*
    - test plan md
    """
    slug = get_file_name_from_url(url)
    artifacts_dir = docs_root / "test-plans" / "artifacts" / slug
    _ensure_dir(artifacts_dir)

    requested_url = url
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(800)
    except Exception:
        # 失败也要落盘最小证据：metadata 标注失败原因
        _write_json(
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
    title = ""
    try:
        title = page.title() or ""
    except Exception:
        title = ""

    # A11y snapshot -> controls
    controls: List[Dict[str, str]] = []
    try:
        snap = page.accessibility.snapshot()
        flat = list(_walk_a11y(snap))
        # 只保留 role/name
        controls = [{"role": x.get("role") or "", "name": x.get("name") or ""} for x in flat if isinstance(x, dict)]
    except Exception:
        controls = []

    redirected_off_origin = bool(final_url) and not _is_same_origin(final_url, origin)
    login_required_suspect = redirected_off_origin or (_is_login_like(final_url) and not _is_login_like(requested_url))
    locator_hints = _build_locator_hints(controls)

    # visible.html / page.png / visible.txt
    try:
        (artifacts_dir / "visible.html").write_text(page.content() or "", encoding="utf-8")
    except Exception:
        (artifacts_dir / "visible.html").write_text("", encoding="utf-8")

    try:
        page.screenshot(path=str(artifacts_dir / "page.png"), full_page=True)
    except Exception:
        pass

    (artifacts_dir / "visible.txt").write_text(
        _render_visible_txt(
            requested_url=requested_url,
            final_url=final_url,
            title=title,
            login_required_suspect=login_required_suspect,
            controls=controls,
        ),
        encoding="utf-8",
    )

    # ABP snapshots（按规则：每页目录各放一份；内容相同，git pack 会去重）
    notes: List[str] = []
    pwd_policy: Dict[str, Any] = {}
    if abp_app_cfg:
        try:
            _write_json(artifacts_dir / "abp_app_config.json", abp_app_cfg)
            pwd_policy = _extract_password_policy_from_abp_app_config(abp_app_cfg)
        except Exception:
            notes.append("abp_app_config_write_failed")
    else:
        notes.append("abp_app_config_unavailable")
    if backend_swagger:
        try:
            _write_json(artifacts_dir / "backend_swagger.json", backend_swagger)
        except Exception:
            notes.append("backend_swagger_write_failed")
    else:
        notes.append("backend_swagger_unavailable")
    if abp_swagger:
        try:
            _write_json(artifacts_dir / "abp_swagger.json", abp_swagger)
        except Exception:
            notes.append("abp_swagger_write_failed")
    else:
        notes.append("abp_swagger_unavailable")

    try:
        _write_json(
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

    # metadata.json（只记录“确实落盘”的证据文件，避免误导）
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

    _write_json(
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

    # page_info -> test plan markdown
    analyzer = PageAnalyzer()
    try:
        page_info = analyzer._analyze_page(page, requested_url)  # noqa: SLF001 (intentional: reuse analyzer logic)
        page_info.auth_required = auth_required
    except Exception:
        # 极端情况下：只生成最小计划
        from generators.page_types import PageInfo

        page_info = PageInfo(url=requested_url, title=title, page_type="FORM", auth_required=auth_required)

    md = TestPlanGenerator().generate(page_info)
    plan_path = docs_root / "test-plans" / f"{slug}.md"
    plan_path.write_text(md, encoding="utf-8")

    return slug


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="", help="config/project.yaml environments.<env> (default=project default)")
    ap.add_argument("--max-pages", type=int, default=80, help="BFS 页面上限（每个上下文）")
    ap.add_argument(
        "--urls-file",
        default="",
        help="按 URL 列表生成（每行一个 URL）；提供后将跳过爬站 BFS",
    )
    ap.add_argument("--headless", action="store_true", default=True)
    ap.add_argument("--headed", action="store_true", default=False, help="显示浏览器窗口（覆盖 headless）")
    args = ap.parse_args()

    cfg = ConfigManager()
    if args.env:
        cfg.set_env(args.env)

    frontend = cfg.get_service_url("frontend") or ""
    backend = cfg.get_service_url("backend") or ""
    if not frontend:
        raise SystemExit("missing frontend base url (config/project.yaml)")

    origin = _canonicalize(frontend).rstrip("/")
    start_url = origin + "/"

    docs_root = Path(__file__).resolve().parent.parent / "docs"
    _ensure_dir(docs_root / "test-plans" / "artifacts")

    headless = True
    if args.headed:
        headless = False
    else:
        headless = bool(args.headless)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_anon = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
        page_anon = ctx_anon.new_page()

        # logged-in context (account pool or env)
        ctx_auth = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
        page_auth = ctx_auth.new_page()

        urls_file = (args.urls_file or "").strip()
        if urls_file:
            # MCP-first: 使用外部枚举出的 URL 列表
            p_urls = Path(urls_file)
            if not p_urls.is_absolute():
                p_urls = (Path(__file__).resolve().parent.parent / p_urls).resolve()
            raw = p_urls.read_text(encoding="utf-8", errors="ignore").splitlines()
            all_urls = sorted({_canonicalize(x.strip()) for x in raw if x.strip().startswith("http")})
            # auth_required：按路由前缀/约定（保守策略：/admin* 认为需要登录态）
            anon_accessible = {u for u in all_urls if urlparse(u).path in {"/", "/workflow"}}

            # 仍然需要准备登录态（用于 /admin* 等受保护页面的“证据链 + 元素识别”）
            # 注意：这里不会把 storageState 落盘，只在运行期使用。
            acc_info = _login_with_account_pool(page_auth)
            logger.info(f"[mcp-urls] login ready: source={acc_info.get('source')}")
        else:
            logger.info(f"[crawl] anonymous start: {start_url}")
            anon_seen, anon_accessible = _crawl_urls(
                page_anon, origin=origin, start_url=start_url, max_pages=max(1, args.max_pages)
            )

            acc_info = _login_with_account_pool(page_auth)
            logger.info(f"[crawl] logged-in: source={acc_info.get('source')}")
            auth_seen, _auth_accessible = _crawl_urls(
                page_auth, origin=origin, start_url=start_url, max_pages=max(1, args.max_pages)
            )

            # union & choose capture context
            all_urls = sorted(set(anon_seen) | set(auth_seen))

        # ABP snapshots（用已登录 context 更稳）
        abp_app_cfg = _try_fetch_json(ctx_auth, f"{origin}/api/abp/application-configuration")
        backend_swagger = _try_fetch_json(ctx_auth, f"{backend.rstrip('/')}/swagger/v1/swagger.json") if backend else None
        abp_swagger = _try_fetch_json(ctx_auth, f"{origin}/swagger/v1/swagger.json")

        # generate per url
        generated: List[Dict[str, Any]] = []
        for u in all_urls:
            path = urlparse(u).path or "/"
            # auth_required：
            # - BFS 模式：匿名访问不可达（被跳到登录/跨域认证）则需要
            # - urls-file 模式：保守按路径前缀判定（/admin* 需要）
            if urls_file:
                auth_required = path.startswith("/admin")
            else:
                auth_required = u not in anon_accessible

            use_page = page_auth if auth_required else page_anon
            slug = _capture_and_generate_one(
                page=use_page,
                url=u,
                origin=_origin_of(u),
                docs_root=docs_root,
                abp_app_cfg=abp_app_cfg,
                backend_swagger=backend_swagger,
                abp_swagger=abp_swagger,
                auth_required=auth_required,
            )
            generated.append({"url": u, "slug": slug, "auth_required": auth_required})

        # index
        index_md = ["# UI Test Plans Index", "", f"- base_url: `{origin}`", ""]
        for x in generated:
            index_md.append(f"- `{x['url']}` -> `docs/test-plans/{x['slug']}.md` (auth_required={x['auth_required']})")
        (docs_root / "test-plans" / "_index.md").write_text("\n".join(index_md) + "\n", encoding="utf-8")
        _write_json(docs_root / "test-plans" / "_index.json", {"base_url": origin, "pages": generated})

        try:
            ctx_anon.close()
            ctx_auth.close()
        except Exception:
            pass
        browser.close()

    logger.info(f"generated test plans: {len(all_urls)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


