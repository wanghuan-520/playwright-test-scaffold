"""
core.fixture

说明：
- 该目录用于承载 fixtures 的实现拆分（按职责分文件），避免 core/fixtures.py 变成上帝文件。
- 对外兼容性：对外仍通过 core/fixtures.py 暴露 fixtures（import path 不变）。
"""


