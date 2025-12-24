"""
# ═══════════════════════════════════════════════════════════════
# MCP Page Analyzer (JSON bridge)
# ═══════════════════════════════════════════════════════════════
#
# 重要事实（请读完再用）：
# --------------------------------------------------------------
# - Cursor 的 Playwright MCP 是“编辑器侧工具会话”，Python 进程无法直接调用。
# - 因此本模块的目标是：把 MCP 导出的 PageInfo JSON 接入 url_flow，
#   让“生成过程使用 MCP 的产物”成为可复现链路。
# --------------------------------------------------------------
#
# 设计取舍：
# - ✅ CLI/CI 可跑：只要 JSON 文件存在
# - ✅ 可审计：会把输入 JSON 复制到 artifacts_dir/incoming_analysis.json
# - ❌ 不能在纯 CLI 环境里自动‘触发 MCP 抓取’（那需要编辑器/Agent 工具）
#
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from generators.page_types import PageInfo, page_info_from_dict
from generators.utils import get_file_name_from_url
from utils.logger import get_logger

logger = get_logger(__name__)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_mcp_pageinfo_path(url: str) -> Path:
    """
    默认落点：test-data/mcp_pageinfo_cache/<url_snake>_pageinfo.json
    例：/admin/profile/change-password -> admin_profile_change_password_pageinfo.json
    """
    root = _project_root()
    slug = get_file_name_from_url(url)
    return root / "test-data" / "mcp_pageinfo_cache" / f"{slug}_pageinfo.json"


class MCPPageAnalyzer:
    """
    MCP Page Analyzer（JSON 桥接）
    
    输入：URL + MCP 导出的 PageInfo JSON
    输出：PageInfo（供 TestCodeGenerator 全量生成）
    """

    def analyze(
        self,
        url: str,
        *,
        mcp_json_path: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
    ) -> PageInfo:
        root = _project_root()

        # ═══════════════════════════════════════════════════════════════
        # 1) Resolve JSON path
        # ═══════════════════════════════════════════════════════════════
        env_path = os.getenv("PT_MCP_PAGEINFO_PATH", "").strip()
        p = (mcp_json_path or "").strip() or env_path
        json_path = Path(p).expanduser() if p else _default_mcp_pageinfo_path(url)
        if not json_path.is_absolute():
            json_path = (root / json_path).resolve()

        wait_seconds = int((os.getenv("PT_MCP_WAIT_SECONDS", "") or "0").strip() or "0")
        if not json_path.exists() and wait_seconds > 0:
            self._wait_for_mcp_json(json_path, wait_seconds=wait_seconds, url=url)

        if not json_path.exists():
            raise SystemExit(
                "MCP PageInfo JSON not found.\n"
                f"- expected: {json_path}\n"
                "\n"
                "How to fix:\n"
                "- 在 Cursor 的 Playwright MCP 中导出 PageInfo JSON 到上述路径；或\n"
                "- 直接传参：--mcp-json <path>；或\n"
                "- 设置环境变量：PT_MCP_PAGEINFO_PATH=<path>\n"
                "\n"
                "Tip:\n"
                "- 你也可以设置：PT_MCP_WAIT_SECONDS=300（让流程先启动并等待你导出 JSON）\n"
            )

        # ═══════════════════════════════════════════════════════════════
        # 2) Load & normalize
        # ═══════════════════════════════════════════════════════════════
        raw_text = json_path.read_text(encoding="utf-8", errors="ignore") or "{}"
        raw_obj: Any = json.loads(raw_text)
        raw_dict: Dict[str, Any] = raw_obj if isinstance(raw_obj, dict) else {}
        page_info = page_info_from_dict(raw_dict)
        if not (page_info.url or "").strip():
            page_info.url = url

        # ═══════════════════════════════════════════════════════════════
        # 3) Audit dump
        # ═══════════════════════════════════════════════════════════════
        self._dump_audit(
            artifacts_dir=artifacts_dir,
            url=url,
            json_path=json_path,
            raw=raw_dict,
            page_info=page_info,
        )

        logger.info(f"MCP analysis loaded: {json_path}")
        return page_info

    def _wait_for_mcp_json(self, json_path: Path, *, wait_seconds: int, url: str) -> None:
        """
        等待 MCP 导出的 PageInfo JSON 出现。

        说明：
        - Python 进程无法直接触发 Cursor Playwright MCP；
        - 这里的“等待”只是为了把人机协作变成“一条命令启动”，避免先手动导出再回来跑命令。
        """
        deadline = time.time() + max(0, int(wait_seconds))
        logger.info(f"waiting for MCP PageInfo JSON (seconds={wait_seconds}): {json_path}")
        print(
            "\n[MCP] waiting for PageInfo JSON...\n"
            f"- url: {url}\n"
            f"- expected: {json_path}\n"
            f"- timeout: {wait_seconds}s\n"
            "请在 Cursor 的 Playwright MCP 中完成分析并导出 PageInfo JSON 到上述路径。\n"
        )
        while time.time() < deadline:
            try:
                if json_path.exists() and json_path.is_file() and json_path.stat().st_size > 0:
                    return
            except Exception:
                pass
            time.sleep(0.5)

    def _dump_audit(
        self,
        *,
        artifacts_dir: Optional[str],
        url: str,
        json_path: Path,
        raw: Dict[str, Any],
        page_info: PageInfo,
    ) -> None:
        if not artifacts_dir:
            return
        try:
            out_dir = Path(artifacts_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"创建 artifacts_dir 失败: {artifacts_dir} err={e}")
            return

        try:
            (out_dir / "analysis_source.txt").write_text(
                f"source=mcp_json\nurl={url}\njson={json_path}\n",
                encoding="utf-8",
            )
        except Exception:
            pass

        # 输入快照（原始 JSON）
        try:
            (out_dir / "incoming_analysis.json").write_text(
                json.dumps(raw, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"写入 incoming_analysis.json 失败: {e}")

        # 解析后快照（PageInfo）
        try:
            (out_dir / "page_info.normalized.json").write_text(
                json.dumps(asdict(page_info), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass


