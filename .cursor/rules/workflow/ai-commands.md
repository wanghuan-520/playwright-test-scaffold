---
alwaysApply: true
---

# AI 对话指令处理

## 测试页面（完整自动化流程）⭐

```
"帮我测试 xxx 页面"
"测试 /admin/profile/change-password"
```

→ 执行完整自动化流程：
1. 页面分析和代码生成（`analysis-and-generation.md`）
2. 自动测试执行（`test-execution.md`）

## 只生成代码（不运行）

```
"生成 xxx 页面的测试代码"
"帮我写 xxx 的测试"
```

→ 只执行：页面分析 + 代码生成（不运行测试）

## 单独运行测试

```
"运行测试"
"执行测试"
```

→ 直接执行测试执行流程（跳过分析和生成）

## 查看报告

```
"打开 Allure 报告"
```

→ 执行 `allure serve allure-results`
