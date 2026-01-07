"""
Spec-driven workflow (spec-kit style) core for this Playwright Test Scaffold.

Design goals:
- Keep existing pipeline intact: docs/test-plans/*.md + artifacts/<slug>/metadata.json -> generators/plan_to_automation.py
- Provide a minimal "specs/" source-of-truth layer (spec/plan/tasks) without any network/LLM dependency.
- Provide incremental commands (per slug) to avoid regenerating everything.

This module intentionally stays < 400 lines.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from generators.mcp_page_analyzer import MCPPageAnalyzer
from generators.test_code_generator import TestCodeGenerator


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def specs_root() -> Path:
    return project_root() / "specs"


def plans_root() -> Path:
    return project_root() / "docs" / "test-plans"


def artifacts_root() -> Path:
    return plans_root() / "artifacts"


def safe_slug(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = s.replace("-", "_")
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unnamed"


def infer_auth_from_url(url: str) -> bool:
    try:
        return (urlparse(url).path or "").startswith("/admin")
    except Exception:
        return False


def next_spec_id(root: Path) -> int:
    if not root.exists():
        return 1
    max_id = 0
    for p in root.glob("*-*"):
        if not p.is_dir():
            continue
        m = re.match(r"^(\d+)-", p.name)
        if not m:
            continue
        try:
            max_id = max(max_id, int(m.group(1)))
        except Exception:
            pass
    return max_id + 1


@dataclass(frozen=True)
class SpecCore:
    slug: str
    url: str
    page_type: str
    auth_required: bool


def parse_spec_core(spec_md: str) -> SpecCore:
    """
    Parse core fields from specs/*/spec.md.

    Expected markers:
    - **slug**: `...`
    - **URL**: `...`
    - **页面类型**: FORM|LOGIN|REGISTER|LIST|...
    - **是否需要登录态**: 是|否
    """
    slug = ""
    url = ""
    page_type = "FORM"
    auth_required = False

    m_slug = re.search(r"\*\*slug\*\*:\s*`([^`]+)`", spec_md)
    if m_slug:
        slug = (m_slug.group(1) or "").strip()

    m_url = re.search(r"\*\*URL\*\*:\s*`([^`]+)`", spec_md)
    if m_url:
        url = (m_url.group(1) or "").strip()

    m_type = re.search(r"\*\*页面类型\*\*:\s*([A-Z_]+)", spec_md)
    if m_type:
        page_type = (m_type.group(1) or "").strip() or "FORM"

    m_auth = re.search(r"\*\*是否需要登录态\*\*:\s*(是|否)", spec_md)
    if m_auth:
        auth_required = True if m_auth.group(1) == "是" else False

    slug = safe_slug(slug)
    if not url:
        raise SystemExit("spec.md missing required field: **URL**: `...`")
    return SpecCore(slug=slug, url=url, page_type=page_type, auth_required=auth_required)


def spec_dir_by_slug(slug: str) -> Path:
    root = specs_root()
    slug = safe_slug(slug)
    candidates = sorted(root.glob(f"*-{slug}"))
    if candidates:
        return candidates[0]
    raise SystemExit(f"spec not found for slug={slug} under {root}")


def ensure_dirs() -> None:
    specs_root().mkdir(parents=True, exist_ok=True)
    plans_root().mkdir(parents=True, exist_ok=True)
    artifacts_root().mkdir(parents=True, exist_ok=True)


def write_if_missing(path: Path, content: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")


def sync_plan_from_core(core: SpecCore, *, force: bool) -> None:
    """
    Ensure docs/test-plans/<slug>.md exists with the minimum contract fields
    required by generators/plan_to_automation.py.
    """
    plan_path = plans_root() / f"{core.slug}.md"
    auth_txt = "是" if core.auth_required else "否"
    md = "\n".join(
        [
            f"# {core.slug} UI 自动化测试计划",
            "",
            "## 0. 生成信息（用于可追溯）",
            f"- **URL**: `{core.url}`",
            f"- **slug**: `{core.slug}`",
            "- **生成时间**: (manual)",
            f"- **是否需要登录态**: {auth_txt}",
            f"- **证据链目录**: `docs/test-plans/artifacts/{core.slug}/`",
            "",
            "## 1. 页面概述",
            f"- **页面类型**: {core.page_type}",
            "- **主要功能（用户任务流）**:",
            "  - TODO",
            "- **风险点**:",
            "  - TODO",
            "",
            "## 2. 页面元素映射",
            "说明：如果你还没有 locator_hints（来自动态分析/MCP），这里先留空；",
            "后续把 `docs/test-plans/artifacts/<slug>/metadata.json` 补齐后再生成代码。",
            "",
            "## 3. 测试用例设计",
            "- TODO",
            "",
        ]
    )
    write_if_missing(plan_path, md + "\n", force=force)


def sync_artifacts_metadata(core: SpecCore, *, force: bool) -> None:
    """
    Ensure docs/test-plans/artifacts/<slug>/metadata.json exists.
    This is optional for generation, but provides locator_hints & audit trail.
    """
    meta_dir = artifacts_root() / core.slug
    meta_path = meta_dir / "metadata.json"
    if meta_path.exists() and not force:
        return
    meta: Dict[str, Any] = {
        "slug": core.slug,
        "url": core.url,
        "final_url": core.url,
        "title": "",
        "auth_required": bool(core.auth_required),
        "evidence_files": ["metadata.json"],
        "locator_hints": {"tabs": {}, "inputs": {}, "buttons": {}, "links": {}},
    }
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_plan_core(plan_md: str) -> Tuple[str, str, Optional[bool]]:
    """
    Parse minimal contract fields from docs/test-plans/<slug>.md:
    - **URL**: `...`
    - **页面类型**: FORM|LOGIN|...
    - **是否需要登录态**: 是|否
    """
    url = ""
    page_type = "FORM"
    auth_required: Optional[bool] = None

    m_url = re.search(r"\*\*URL\*\*:\s*`([^`]+)`", plan_md)
    if m_url:
        url = (m_url.group(1) or "").strip()

    m_type = re.search(r"\*\*页面类型\*\*:\s*([A-Z_]+)", plan_md)
    if m_type:
        page_type = (m_type.group(1) or "").strip() or "FORM"

    m_auth = re.search(r"\*\*是否需要登录态\*\*:\s*(是|否)", plan_md)
    if m_auth:
        auth_required = True if m_auth.group(1) == "是" else False

    return url, page_type, auth_required


def sync_index(*, base_url: Optional[str] = None) -> None:
    """
    Rebuild docs/test-plans/_index.md (best-effort).
    """
    p_root = plans_root()
    a_root = artifacts_root()
    pages = []
    for plan in sorted(p_root.glob("*.md")):
        if plan.name.startswith("_"):
            continue
        slug = plan.stem
        auth_required: Optional[bool] = None
        meta_path = a_root / slug / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8", errors="ignore") or "{}")
                if isinstance(meta.get("auth_required"), bool):
                    auth_required = bool(meta["auth_required"])
            except Exception:
                pass
        pages.append({"slug": slug, "auth_required": auth_required})

    base = base_url or "https://localhost:3000"
    lines = ["# UI Test Plans Index", "", f"- base_url: `{base}`", ""]
    for x in pages:
        auth_txt = "unknown" if x["auth_required"] is None else str(bool(x["auth_required"]))
        lines.append(f"- `({x['slug']})` -> `docs/test-plans/{x['slug']}.md` (auth_required={auth_txt})")
    (p_root / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_new(args: argparse.Namespace) -> int:
    ensure_dirs()
    slug = safe_slug(args.slug)
    url = (args.url or "").strip()
    if not url:
        raise SystemExit("--url is required")
    page_type = (args.page_type or "FORM").strip().upper()
    auth_required = bool(args.auth_required) if args.auth_required is not None else infer_auth_from_url(url)

    spec_id = next_spec_id(specs_root())
    spec_dir = specs_root() / f"{spec_id:03d}-{slug}"
    spec_dir.mkdir(parents=True, exist_ok=True)

    auth_txt = "是" if auth_required else "否"
    spec_md = "\n".join(
        [
            f"# {slug} - Spec",
            "",
            "## 0. 核心信息",
            f"- **slug**: `{slug}`",
            f"- **URL**: `{url}`",
            f"- **页面类型**: {page_type}",
            f"- **是否需要登录态**: {auth_txt}",
            "",
            "## 1. 用户目标（User Story）",
            "- TODO: 作为...我希望...以便...",
            "",
            "## 2. 范围（In/Out）",
            "- **In**: TODO",
            "- **Out**: TODO",
            "",
            "## 3. 风险与不可逆操作（Risk）",
            "- TODO",
            "",
            "## 4. 验收标准（Acceptance Criteria）",
            "- TODO",
            "",
        ]
    )
    plan_md = "\n".join(
        [
            f"# {slug} - Plan",
            "",
            "## 0. 输入/输出",
            f"- **输入 spec**: `specs/{spec_dir.name}/spec.md`",
            f"- **输入 plan（契约）**: `docs/test-plans/{slug}.md`",
            f"- **证据链目录**: `docs/test-plans/artifacts/{slug}/`",
            "- **输出代码**: `pages/` + `tests/` + `test-data/`",
            "",
            "## 1. 执行步骤（最短闭环）",
            f"- 同步 plan stub：`make spec-plan SLUG={slug}`",
            f"- （可选）补齐定位器证据：artifacts/{slug}/metadata.json 或 MCP JSON",
            f"- 生成代码：`make spec-implement SLUG={slug} MODE=plan`",
            "",
        ]
    )
    tasks_md = "\n".join(
        [
            f"# {slug} - Tasks",
            "",
            "- [ ] 填写 `spec.md` 的 user story / AC",
            "- [ ] 确认 `docs/test-plans/<slug>.md` 的 URL/页面类型/登录态正确",
            "- [ ] 补齐 `metadata.json` 的 locator_hints（来自动态分析/MCP）",
            "- [ ] 生成套件：`make spec-implement SLUG=<slug> MODE=plan`",
            "- [ ] 跑通：`make test TEST_TARGET=tests/...` 并检查 Allure",
            "",
        ]
    )
    write_if_missing(spec_dir / "spec.md", spec_md + "\n", force=bool(args.force))
    write_if_missing(spec_dir / "plan.md", plan_md + "\n", force=bool(args.force))
    write_if_missing(spec_dir / "tasks.md", tasks_md + "\n", force=bool(args.force))

    core = SpecCore(slug=slug, url=url, page_type=page_type, auth_required=auth_required)
    if not args.no_plan:
        sync_plan_from_core(core, force=bool(args.force))
        sync_artifacts_metadata(core, force=bool(args.force))
        sync_index(base_url=args.base_url)
    print(f"created spec: {spec_dir}")
    return 0


def cmd_sync_plan(args: argparse.Namespace) -> int:
    ensure_dirs()
    spec_dir = spec_dir_by_slug(args.slug)
    core = parse_spec_core((spec_dir / "spec.md").read_text(encoding="utf-8", errors="ignore"))
    sync_plan_from_core(core, force=bool(args.force))
    sync_artifacts_metadata(core, force=bool(args.force))
    sync_index(base_url=args.base_url)
    print(f"synced plan/artifacts for slug={core.slug}")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """
    Create specs/<NNN>-<slug>/ for existing docs/test-plans/<slug>.md.
    Never overwrites existing plans by default.
    """
    ensure_dirs()
    p_root = plans_root()
    slugs = [p.stem for p in sorted(p_root.glob("*.md")) if not p.name.startswith("_")]

    created = 0
    skipped = 0
    for slug in slugs:
        slug = safe_slug(slug)
        # already bootstrapped?
        if sorted(specs_root().glob(f"*-{slug}")):
            skipped += 1
            continue

        plan_path = p_root / f"{slug}.md"
        plan_md = plan_path.read_text(encoding="utf-8", errors="ignore") or ""
        url, page_type, auth = parse_plan_core(plan_md)
        if not url:
            # Without URL, we can't produce a meaningful spec core.
            skipped += 1
            continue
        auth_required = bool(auth) if isinstance(auth, bool) else infer_auth_from_url(url)

        # create spec folder (without touching plan)
        spec_id = next_spec_id(specs_root())
        spec_dir = specs_root() / f"{spec_id:03d}-{slug}"
        spec_dir.mkdir(parents=True, exist_ok=True)

        auth_txt = "是" if auth_required else "否"
        spec_md = "\n".join(
            [
                f"# {slug} - Spec",
                "",
                "## 0. 核心信息",
                f"- **slug**: `{slug}`",
                f"- **URL**: `{url}`",
                f"- **页面类型**: {page_type}",
                f"- **是否需要登录态**: {auth_txt}",
                "",
                "## 1. 用户目标（User Story）",
                "- TODO",
                "",
                "## 2. 范围（In/Out）",
                "- **In**: TODO",
                "- **Out**: TODO",
                "",
                "## 3. 验收标准（Acceptance Criteria）",
                "- TODO",
                "",
            ]
        )
        plan_md2 = "\n".join(
            [
                f"# {slug} - Plan",
                "",
                "## 0. 关联产物",
                f"- **plan（契约）**: `docs/test-plans/{slug}.md`",
                f"- **证据链目录**: `docs/test-plans/artifacts/{slug}/`",
                "",
                "## 1. 执行步骤",
                f"- 生成代码：`make spec-implement SLUG={slug} MODE=plan`",
                "",
            ]
        )
        tasks_md = "\n".join(
            [
                f"# {slug} - Tasks",
                "",
                "- [ ] 补齐 spec 的 user story / AC",
                f"- [ ] 确认证据链：`docs/test-plans/artifacts/{slug}/metadata.json`",
                f"- [ ] 生成/刷新代码：`make spec-implement SLUG={slug} MODE=plan`",
                "",
            ]
        )
        write_if_missing(spec_dir / "spec.md", spec_md + "\n", force=False)
        write_if_missing(spec_dir / "plan.md", plan_md2 + "\n", force=False)
        write_if_missing(spec_dir / "tasks.md", tasks_md + "\n", force=False)
        created += 1

    sync_index(base_url=args.base_url)
    print(f"bootstrap done: created={created} skipped={skipped}")
    return 0


def cmd_implement(args: argparse.Namespace) -> int:
    root = project_root()
    mode = (args.mode or "plan").strip().lower()
    slug = safe_slug(args.slug)

    if mode == "plan":
        import subprocess

        cmd = [
            "python3",
            "-m",
            "generators.plan_to_automation",
            "--plans-dir",
            str(plans_root()),
            "--slug",
            slug,
        ]
        if bool(args.overwrite):
            cmd.append("--overwrite")
        raise SystemExit(subprocess.call(cmd, cwd=str(root)))

    if mode == "mcp":
        spec_dir = spec_dir_by_slug(slug)
        core = parse_spec_core((spec_dir / "spec.md").read_text(encoding="utf-8", errors="ignore"))
        artifacts_dir = str(artifacts_root() / core.slug)
        page_info = MCPPageAnalyzer().analyze(core.url, mcp_json_path=args.mcp_json, artifacts_dir=artifacts_dir)
        page_info.auth_required = bool(core.auth_required)
        TestCodeGenerator().generate_all(page_info, output_dir=str(root))
        print(f"implemented from mcp: slug={core.slug}")
        return 0

    raise SystemExit(f"unknown mode: {mode} (expected: plan|mcp)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="speckit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="Create a new spec folder (and optional plan/artifacts stub).")
    p_new.add_argument("--slug", required=True)
    p_new.add_argument("--url", required=True)
    p_new.add_argument("--page-type", default="FORM")
    p_new.add_argument(
        "--auth-required",
        default=None,
        choices=["true", "false"],
        help="Override auth_required; default infers from URL (/admin*).",
    )
    p_new.add_argument("--no-plan", action="store_true", default=False)
    p_new.add_argument("--base-url", default="")
    p_new.add_argument("--force", action="store_true", default=False)
    p_new.set_defaults(func=cmd_new)

    p_sync = sub.add_parser("sync-plan", help="Sync docs/test-plans + artifacts from an existing spec.")
    p_sync.add_argument("--slug", required=True)
    p_sync.add_argument("--base-url", default="")
    p_sync.add_argument("--force", action="store_true", default=False)
    p_sync.set_defaults(func=cmd_sync_plan)

    p_boot = sub.add_parser("bootstrap", help="Create specs/ folders from existing docs/test-plans/*.md.")
    p_boot.add_argument("--base-url", default="")
    p_boot.set_defaults(func=cmd_bootstrap)

    p_impl = sub.add_parser("implement", help="Generate code from plan markdown or MCP json.")
    p_impl.add_argument("--slug", required=True)
    p_impl.add_argument("--mode", default="plan", choices=["plan", "mcp"])
    p_impl.add_argument("--overwrite", action="store_true", default=False)
    p_impl.add_argument("--mcp-json", default="", help="Optional MCP PageInfo JSON path (mode=mcp).")
    p_impl.set_defaults(func=cmd_implement)

    return ap


