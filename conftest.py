# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Root Conftest (Shared Session)
# ═══════════════════════════════════════════════════════════════

import sys
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入核心fixtures
from core.fixtures import *

# 导入共享session fixtures
from core.shared_session_v2 import *
