"""
Spec-driven workflow (spec-kit style) entrypoint for this Playwright Test Scaffold.

This file is intentionally tiny:
- Makefile calls this path (`scripts/speckit.py`)
- Real logic lives in `scripts/speckit_core.py` (kept < 400 lines)
"""

from __future__ import annotations

import sys
from pathlib import Path

#
# ═══════════════════════════════════════════════════════════════
# sys.path bootstrap
# - Allow running via absolute path / arbitrary cwd
# - Ensure repo root is importable (generators/, scripts/ namespace package)
# ═══════════════════════════════════════════════════════════════
#
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.speckit_core import build_parser  # noqa: E402


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()

    # normalize auth flag (argparse optional boolean)
    if getattr(args, "auth_required", None) is not None:
        args.auth_required = True if args.auth_required == "true" else False

    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())


