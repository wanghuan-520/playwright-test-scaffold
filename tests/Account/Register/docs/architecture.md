# Account/Register 测试架构（局部）

目标：让 Register 的“约束验证/已知缺陷/证据采集”在 Allure 中清晰呈现，同时保持每个文件短小（<400 行）。

## 目录结构

```
tests/Account/Register/
  docs/
    architecture.md
  _abp_constraints_helpers.py
  _helpers.py
  test_Register_p1_abp_constraints.py
  test_Register_known_bugs.py
  ...
```

## 文件职责

- `test_Register_p1_abp_constraints.py`：面向 Allure 的“用例集合”，只保留测试用例本体（边界值、必填/最小值、已知缺陷 xfail），不再堆工具函数。
- `_abp_constraints_helpers.py`：上述用例依赖的**构造器/断言/描述文本**聚合处；保证 test 文件读起来像“测试计划”，而不是“工具箱”。
- `test_Register_known_bugs.py`：历史入口保留，但模块级 `skip`；已知缺陷用例已合并到 `test_Register_p1_abp_constraints.py`，避免重复收集与报告割裂。

## 设计取舍（Why）

- **证据驱动**：UI error / 4xx / 截断前后值对比是最可审计的信号，比依赖浏览器 `validationMessage` 更稳定。
- **并行友好**：拆成多条参数化用例，让 `pytest-xdist -n 4` 能真正分摊。
- **文件短小**：工具函数抽离到 `_abp_constraints_helpers.py`，保持单文件可维护性与审阅体验。


