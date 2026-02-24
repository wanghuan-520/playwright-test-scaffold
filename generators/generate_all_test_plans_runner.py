"""
Generate-all-test-plans orchestration runner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from playwright.sync_api import Page, sync_playwright

from generators.generate_all_test_plans_evidence import capture_and_generate_one, ensure_dir, try_fetch_json, write_json
from generators.generate_all_test_plans_url import canonicalize, crawl_urls, is_login_like, is_same_origin, origin_of
from pages.login_page import LoginPage
from utils.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


def login_with_account_pool(page: Page) -> Dict[str, str]:
    """使用环境变量或账号池登录（运行期登录，不落盘 state）。"""
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
    return {
        "username": str(acc.get("username") or ""),
        "email": str(acc.get("email") or ""),
        "source": "account_pool",
    }


def resolve_all_urls(
    *,
    urls_file: str,
    origin: str,
    start_url: str,
    max_pages: int,
    page_anon: Page,
    page_auth: Page,
) -> Tuple[List[str], set[str], str]:
    """解析待生成 URL 列表，返回 (all_urls, anon_accessible, mode)。"""
    if urls_file:
        p_urls = Path(urls_file)
        if not p_urls.is_absolute():
            p_urls = (Path(__file__).resolve().parent.parent / p_urls).resolve()
        raw = p_urls.read_text(encoding="utf-8", errors="ignore").splitlines()
        all_urls = sorted({canonicalize(x.strip()) for x in raw if x.strip().startswith("http")})
        anon_accessible = {u for u in all_urls if urlparse(u).path in {"/", "/workflow"}}
        return all_urls, anon_accessible, "mcp_urls"

    logger.info(f"[crawl] anonymous start: {start_url}")
    anon_seen, anon_accessible = crawl_urls(
        page_anon, origin=origin, start_url=start_url, max_pages=max(1, max_pages)
    )
    acc_info = login_with_account_pool(page_auth)
    logger.info(f"[crawl] logged-in: source={acc_info.get('source')}")
    auth_seen, _auth_accessible = crawl_urls(
        page_auth, origin=origin, start_url=start_url, max_pages=max(1, max_pages)
    )
    all_urls = sorted(set(anon_seen) | set(auth_seen))
    return all_urls, anon_accessible, "crawl"


def run_generation(*, frontend: str, backend: str, max_pages: int, urls_file: str, headless: bool) -> int:
    origin = canonicalize(frontend).rstrip("/")
    start_url = origin + "/"
    docs_root = Path(__file__).resolve().parent.parent / "docs"
    ensure_dir(docs_root / "test-plans" / "artifacts")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_anon = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
        page_anon = ctx_anon.new_page()
        ctx_auth = browser.new_context(ignore_https_errors=True, viewport={"width": 1920, "height": 1080})
        page_auth = ctx_auth.new_page()

        all_urls, anon_accessible, mode = resolve_all_urls(
            urls_file=urls_file,
            origin=origin,
            start_url=start_url,
            max_pages=max_pages,
            page_anon=page_anon,
            page_auth=page_auth,
        )
        if mode == "mcp_urls":
            acc_info = login_with_account_pool(page_auth)
            logger.info(f"[mcp-urls] login ready: source={acc_info.get('source')}")

        abp_app_cfg = try_fetch_json(ctx_auth, f"{origin}/api/abp/application-configuration")
        backend_swagger = try_fetch_json(ctx_auth, f"{backend.rstrip('/')}/swagger/v1/swagger.json") if backend else None
        abp_swagger = try_fetch_json(ctx_auth, f"{origin}/swagger/v1/swagger.json")

        generated: List[Dict[str, Any]] = []
        for u in all_urls:
            path = urlparse(u).path or "/"
            auth_required = path.startswith("/admin") if urls_file else (u not in anon_accessible)
            use_page = page_auth if auth_required else page_anon
            current_origin = origin_of(u)
            slug = capture_and_generate_one(
                page=use_page,
                url=u,
                is_same_origin_fn=lambda x, o=current_origin: is_same_origin(x, o),
                is_login_like_fn=is_login_like,
                docs_root=docs_root,
                abp_app_cfg=abp_app_cfg,
                backend_swagger=backend_swagger,
                abp_swagger=abp_swagger,
                auth_required=auth_required,
            )
            generated.append({"url": u, "slug": slug, "auth_required": auth_required})

        index_md = ["# UI Test Plans Index", "", f"- base_url: `{origin}`", ""]
        for x in generated:
            index_md.append(f"- `{x['url']}` -> `docs/test-plans/{x['slug']}.md` (auth_required={x['auth_required']})")
        (docs_root / "test-plans" / "_index.md").write_text("\n".join(index_md) + "\n", encoding="utf-8")
        write_json(docs_root / "test-plans" / "_index.json", {"base_url": origin, "pages": generated})

        try:
            ctx_anon.close()
            ctx_auth.close()
        except Exception:
            pass
        browser.close()

    logger.info(f"generated test plans: {len(all_urls)} pages")
    return 0
