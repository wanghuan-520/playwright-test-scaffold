"""
Generate-all-test-plans URL and link helpers.
"""

from __future__ import annotations

from typing import List, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.sync_api import Page

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


def canonicalize(url: str) -> str:
    """归一化 URL：去 query/fragment，规范 path 结尾。"""
    p = urlparse(url)
    path = p.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((p.scheme, p.netloc, path, "", "", ""))


def is_same_origin(url: str, origin: str) -> bool:
    u = urlparse(url)
    o = urlparse(origin)
    return (u.scheme, u.netloc) == (o.scheme, o.netloc)


def origin_of(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def is_probably_asset(url: str) -> bool:
    p = urlparse(url)
    path = (p.path or "").lower()
    if not path:
        return False
    if path.startswith("/_next/") or path.startswith("/static/") or path.startswith("/assets/"):
        return True
    return any(path.endswith(ext) for ext in _ASSET_EXTS)


def is_login_like(url: str) -> bool:
    path = (urlparse(url).path or "").lower()
    return any(x in path for x in ["/account/login", "/auth/login", "/login", "/signin"])


def extract_links(page: Page, *, origin: str) -> List[str]:
    """抽取当前页同源可访问链接。"""
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
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue

        abs_url = canonicalize(urljoin(origin, href))
        if not abs_url.startswith("http"):
            continue
        if not is_same_origin(abs_url, origin):
            continue
        if is_probably_asset(abs_url):
            continue
        hrefs.append(abs_url)
    return hrefs


def crawl_urls(page: Page, *, origin: str, start_url: str, max_pages: int) -> Tuple[Set[str], Set[str]]:
    """BFS 爬站：返回 (seen, anonymous_accessible)。"""
    q: List[str] = [canonicalize(start_url)]
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

        try:
            final_url = page.url or ""
        except Exception:
            final_url = ""
        redirected_off_origin = bool(final_url) and not is_same_origin(final_url, origin)
        login_redirect = redirected_off_origin or (is_login_like(final_url) and not is_login_like(url))
        if not login_redirect:
            accessible.add(url)

        for u in extract_links(page, origin=origin):
            if u not in seen:
                q.append(u)

    return seen, accessible
