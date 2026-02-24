"""
Generate UI test plans for reachable pages (entrypoint).
"""

from __future__ import annotations

import argparse

from generators.generate_all_test_plans_runner import run_generation
from utils.config import ConfigManager


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="", help="config/project.yaml environments.<env> (default=project default)")
    ap.add_argument("--max-pages", type=int, default=80, help="BFS 页面上限（每个上下文）")
    ap.add_argument("--urls-file", default="", help="按 URL 列表生成（每行一个 URL）；提供后将跳过爬站 BFS")
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

    headless = False if args.headed else bool(args.headless)
    return run_generation(
        frontend=frontend,
        backend=backend,
        max_pages=max(1, args.max_pages),
        urls_file=(args.urls_file or "").strip(),
        headless=headless,
    )


if __name__ == "__main__":
    raise SystemExit(main())
