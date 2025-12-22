"""
# ═══════════════════════════════════════════════════════════════
# Rules Loader - 将 .cursor/rules 变成“可执行入口可读取的运行时上下文”
# ═══════════════════════════════════════════════════════════════
#
# 背景：
# - `.cursor/rules/**` 是 Cursor/AI 对话侧的规则系统（Markdown + front matter）
# - 但我们这套 Python 生成链路（tools/url_flow.py）不会“自动读取规则”
# - 为了让“生成过程调用 rule”变成可验证事实：在运行时加载并落盘规则上下文
#
# 设计目标：
# - 不引入新依赖
# - 可审计：输出 sources 列表 + hash + 合并后的文本
# - 可控：允许 caller 关闭或指定输出路径
#
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class RuleSource:
    path: str
    sha256: str
    bytes_len: int


@dataclass(frozen=True)
class RulesContext:
    sources: List[RuleSource]
    combined_markdown: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_rule_paths(root: Path) -> List[Path]:
    """
    按 `.cursor/rules/project/index.md` 描述的优先级组织（尽量稳定、可预期）。
    注意：这些文件可能不存在（允许缺失），会被过滤。
    """
    return [
        root / ".cursor" / "rules" / "core" / "project-overview.md",
        root / "docs" / "requirements.md",
        root / ".cursor" / "rules" / "workflow" / "analysis-and-generation.md",
        root / ".cursor" / "rules" / "workflow" / "test-execution.md",
        root / ".cursor" / "rules" / "workflow" / "ai-commands.md",
        root / ".cursor" / "rules" / "generation" / "code-generation.md",
        root / ".cursor" / "rules" / "quality" / "test-case-standards.md",
        root / ".cursor" / "rules" / "quality" / "allure-reporting.md",
        root / ".cursor" / "rules" / "data" / "data-management.md",
        root / ".cursor" / "rules" / "project" / "index.md",
    ]


def _dedupe_paths(paths: Iterable[Path]) -> List[Path]:
    seen = set()
    out: List[Path] = []
    for p in paths:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p)
    return out


def load_rules_context(
    *,
    root: Optional[Path] = None,
    extra_paths: Optional[List[Path]] = None,
) -> RulesContext:
    """
    读取规则文件并合并成一个 Markdown 上下文。
    """
    r = root or _project_root()
    paths = _default_rule_paths(r)
    if extra_paths:
        paths.extend(extra_paths)
    paths = _dedupe_paths(paths)

    sources: List[RuleSource] = []
    chunks: List[str] = []

    for p in paths:
        if not p.exists() or not p.is_file():
            continue
        raw = p.read_bytes()
        sources.append(RuleSource(path=str(p.relative_to(r)), sha256=_sha256(raw), bytes_len=len(raw)))
        text = _read_text(p).strip()
        chunks.append(
            "\n".join(
                [
                    "",
                    "<!-- ═══════════════════════════════════════════════════════ -->",
                    f"<!-- SOURCE: {p.relative_to(r)} -->",
                    f"<!-- SHA256: {_sha256(raw)} -->",
                    "<!-- ═══════════════════════════════════════════════════════ -->",
                    "",
                    text,
                    "",
                ]
            )
        )

    combined = "\n".join(chunks).lstrip()
    return RulesContext(sources=sources, combined_markdown=combined)


def write_rules_context(ctx: RulesContext, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(ctx.combined_markdown, encoding="utf-8")


