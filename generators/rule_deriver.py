# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Rule Deriver
# ═══════════════════════════════════════════════════════════════
"""从前后端代码推导字段校验规则。

目标（强制规则）：
- 有前端/后端本地代码路径时：必须推导出字段规则并写入生成的测试（# Source 可追溯）。
- 推导失败时：禁止“凭猜”生成边界/格式用例（应显式报错或在测试里 skip 并说明来源缺失）。

实现策略（务实、可演进）：
- 先做最小可用的 react-hook-form register() 解析：required/minLength/maxLength/pattern。
- 结合 DOM 动态信息补全 selector/type（不把动态当真理，只当定位/兜底）。
- 后端 ABP DTO/Attribute 的解析先做轻量级（StringLength/Required/EmailAddress），可逐步增强。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re

from generators.page_types import PageInfo, PageElement
from generators.utils import extract_url_path
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RuleSource:
    kind: str  # frontend|backend|dynamic
    path: str
    detail: str = ""


@dataclass
class FieldRule:
    field: str
    selector: str = ""
    required: Optional[bool] = None
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    pattern: Optional[str] = None
    html_type: Optional[str] = None
    sources: List[RuleSource] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["sources"] = [asdict(s) for s in self.sources]
        return d


class RuleDeriver:
    def __init__(self, frontend_root: Optional[str], backend_root: Optional[str]):
        self.frontend_root = Path(frontend_root).expanduser() if frontend_root else None
        self.backend_root = Path(backend_root).expanduser() if backend_root else None

    @classmethod
    def from_config(cls, cfg: ConfigManager) -> "RuleDeriver":
        # 兼容：即使 ConfigManager 默认 config 没这些 key，也允许通过 project.yaml 提供
        fe = cfg.get("repositories.frontend.local_path", "")
        be = cfg.get("repositories.backend.local_path", "")
        fe = fe or None
        be = be or None
        return cls(fe, be)

    def derive(self, page_info: PageInfo) -> List[Dict[str, Any]]:
        """返回可 JSON 化的规则列表（用于写入生成的测试/辅助文件）。"""
        url_path = extract_url_path(page_info.url)

        dyn = self._derive_from_dynamic(page_info)
        fe = self._derive_from_frontend(url_path) if self.frontend_root and self.frontend_root.exists() else {}
        be = self._derive_from_backend(list(fe.keys()) or list(dyn.keys())) if self.backend_root and self.backend_root.exists() else {}

        merged: Dict[str, FieldRule] = {}

        def upsert(key: str, patch: FieldRule) -> None:
            base = merged.get(key)
            if base is None:
                merged[key] = patch
                return
            # selector/html_type 优先用动态（更贴近当前页面），规则优先用静态
            if patch.selector and not base.selector:
                base.selector = patch.selector
            if patch.html_type and not base.html_type:
                base.html_type = patch.html_type
            for attr in ["required", "min_len", "max_len", "pattern"]:
                val = getattr(patch, attr)
                if val is not None and getattr(base, attr) is None:
                    setattr(base, attr, val)
            base.sources.extend(patch.sources)

        for k, r in dyn.items():
            upsert(k, r)
        for k, r in fe.items():
            upsert(k, r)
        for k, r in be.items():
            upsert(k, r)

        # 仅保留“能定位”的字段：没 selector 的规则在测试里没法用
        out = [r.to_dict() for r in merged.values() if r.selector]
        out.sort(key=lambda x: x.get("field") or "")
        return out

    # ═══════════════════════════════════════════════════════════════
    # Dynamic (DOM) hints
    # ═══════════════════════════════════════════════════════════════

    def _derive_from_dynamic(self, page_info: PageInfo) -> Dict[str, FieldRule]:
        rules: Dict[str, FieldRule] = {}
        for e in page_info.elements:
            if e.type != "input":
                continue
            key = self._field_key_from_element(e)
            if not key:
                continue
            html_type = (e.attributes or {}).get("type") or None
            r = FieldRule(
                field=key,
                selector=e.selector,
                required=True if e.required else None,
                html_type=html_type,
                sources=[RuleSource(kind="dynamic", path="(dom)", detail="PageAnalyzer element")],
            )
            rules[key] = r
        return rules

    def _field_key_from_element(self, e: PageElement) -> str:
        for cand in [e.name, e.id, (e.attributes or {}).get("name", "")]:
            cand = (cand or "").strip()
            if cand:
                return cand
        # fallback: try selector like #email
        sel = (e.selector or "").strip()
        if sel.startswith("#") and len(sel) > 1:
            return sel[1:]
        return ""

    # ═══════════════════════════════════════════════════════════════
    # Frontend (react-hook-form) parsing
    # ═══════════════════════════════════════════════════════════════

    def _derive_from_frontend(self, url_path: str) -> Dict[str, FieldRule]:
        candidates = self._candidate_frontend_files(url_path)
        rules: Dict[str, FieldRule] = {}
        for fp in candidates:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for m in re.finditer(r"register\(\s*['\"](?P<field>[A-Za-z0-9_]+)['\"]\s*,\s*\{(?P<body>[\s\S]*?)\}\s*\)", text):
                field_name = m.group("field")
                body = m.group("body")

                required = self._parse_required(body)
                min_len = self._parse_len(body, "minLength")
                max_len = self._parse_len(body, "maxLength")
                pattern = self._parse_pattern(body)
                html_type = self._parse_html_type_around(text, m.start())

                src_detail = "react-hook-form register()"
                src = RuleSource(kind="frontend", path=str(fp), detail=src_detail)

                fr = FieldRule(
                    field=field_name,
                    required=required,
                    min_len=min_len,
                    max_len=max_len,
                    pattern=pattern,
                    html_type=html_type,
                    sources=[src],
                )
                rules[field_name] = fr

        # selector 仍需由 dynamic 补全，因此这里不填 selector
        return rules

    def _candidate_frontend_files(self, url_path: str) -> List[Path]:
        root = self.frontend_root
        if root is None:
            return []

        segments = [s for s in url_path.strip("/").split("/") if s]
        last = segments[-1] if segments else ""

        direct: List[Path] = []

        # Next.js app router
        if segments:
            direct.append(root / "src" / "app" / Path(*segments) / "page.tsx")
            direct.append(root / "app" / Path(*segments) / "page.tsx")

        # Next.js pages router / plain React pages
        if segments:
            direct.append(root / "src" / "pages" / Path(*segments) / "index.tsx")
            direct.append(root / "src" / "pages" / f"{last}.tsx")
            direct.append(root / "pages" / Path(*segments) / "index.tsx")
            direct.append(root / "pages" / f"{last}.tsx")

        existing = [p for p in direct if p.exists() and p.is_file()]
        if existing:
            return existing

        # Fallback: scoped scan under src/ for files likely related to last segment
        scan_root = None
        for cand in [root / "src", root]:
            if cand.exists() and cand.is_dir():
                scan_root = cand
                break
        if scan_root is None:
            return []

        hits: List[Path] = []
        max_files = 2000
        exts = {".ts", ".tsx", ".js", ".jsx"}

        for fp in scan_root.rglob("*"):
            if len(hits) >= 50:
                break
            if not fp.is_file() or fp.suffix not in exts:
                continue
            name = fp.name.lower()
            if last and last.lower() not in name:
                continue
            try:
                head = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "register(" in head:
                hits.append(fp)
            max_files -= 1
            if max_files <= 0:
                break

        return hits

    def _parse_required(self, body: str) -> Optional[bool]:
        m = re.search(r"\brequired\s*:\s*(true|false)", body)
        if m:
            return m.group(1) == "true"
        # required: "message" or required: { value: true }
        m = re.search(r"\brequired\s*:\s*['\"]", body)
        if m:
            return True
        m = re.search(r"\brequired\s*:\s*\{[\s\S]*?\bvalue\s*:\s*(true|false)", body)
        if m:
            return m.group(1) == "true"
        return None

    def _parse_len(self, body: str, key: str) -> Optional[int]:
        # maxLength: 64
        m = re.search(rf"\b{re.escape(key)}\s*:\s*(\d+)", body)
        if m:
            return int(m.group(1))
        # maxLength: { value: 64, message: ... }
        m = re.search(rf"\b{re.escape(key)}\s*:\s*\{{[\s\S]*?\bvalue\s*:\s*(\d+)", body)
        if m:
            return int(m.group(1))
        return None

    def _parse_pattern(self, body: str) -> Optional[str]:
        # pattern: /.../
        m = re.search(r"\bpattern\s*:\s*(/[^/\n]+/[gimuy]*)", body)
        if m:
            return m.group(1)
        # pattern: { value: /.../ }
        m = re.search(r"\bpattern\s*:\s*\{[\s\S]*?\bvalue\s*:\s*(/[^/\n]+/[gimuy]*)", body)
        if m:
            return m.group(1)
        return None

    def _parse_html_type_around(self, text: str, idx: int) -> Optional[str]:
        window = text[max(0, idx - 300) : min(len(text), idx + 300)]
        m = re.search(r"\btype\s*=\s*['\"]([a-zA-Z0-9_-]+)['\"]", window)
        return m.group(1) if m else None

    # ═══════════════════════════════════════════════════════════════
    # Backend (ABP DTO/Attribute) parsing - lightweight
    # ═══════════════════════════════════════════════════════════════

    def _derive_from_backend(self, field_names: List[str]) -> Dict[str, FieldRule]:
        root = self.backend_root
        if root is None:
            return {}

        # 轻量扫描：只看 .cs，并优先含 MyProfile/Profile 字样的文件
        cs_files: List[Path] = []
        for fp in root.rglob("*.cs"):
            if len(cs_files) >= 400:
                break
            low = fp.name.lower()
            if "profile" in low or "account" in low or "user" in low:
                cs_files.append(fp)

        rules: Dict[str, FieldRule] = {}

        for fp in cs_files:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for field_name in field_names:
                # property name in C# often PascalCase
                prop = self._to_pascal(field_name)
                # capture attribute block + property line
                m = re.search(
                    rf"(?P<attrs>(?:\s*\[[^\]]+\]\s*)+)\s*public\s+[A-Za-z0-9_<>\[\]]+\s+{re.escape(prop)}\s*\{{",
                    text,
                )
                if not m:
                    continue

                attrs = m.group("attrs")
                required = True if re.search(r"\[\s*Required\s*(\(|\])", attrs) else None
                max_len = None
                sm = re.search(r"\[\s*StringLength\s*\(\s*(\d+)", attrs)
                if sm:
                    max_len = int(sm.group(1))

                email_attr = True if re.search(r"\[\s*EmailAddress\s*(\(|\])", attrs) else None

                src = RuleSource(kind="backend", path=str(fp), detail="DTO attributes")
                fr = FieldRule(field=field_name, required=required, max_len=max_len, sources=[src])
                if email_attr:
                    fr.html_type = "email"
                rules[field_name] = fr

        return rules

    def _to_pascal(self, s: str) -> str:
        if not s:
            return s
        parts = re.split(r"[^A-Za-z0-9]+", s)
        parts = [p for p in parts if p]
        if not parts:
            return s[:1].upper() + s[1:]
        return "".join(p[:1].upper() + p[1:] for p in parts)
