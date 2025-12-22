---
alwaysApply: true
---
# Cursor Project Rules (always apply)
# 目标：让自然语言“测试 URL”默认生成完整用例集

## 默认行为（强制）
- 当用户输入类似：
  - “帮我测试下https://localhost:3000/admin/profile”
  - “帮我测试 https://.../admin/profile”
  - “测试 /admin/profile”
  - “测试下 https://localhost:3000/admin/profile”
  - “测试下URL：https://localhost:3000/admin/profile”
  - “测试下 个人资料页面”
  - “测试下 XX页面”
  统一按【完整自动化流程】执行：
  1) 页面分析（优先带登录态：使用 `.auth/storage_state.json` / `auth_page` 思路，避免每条用例都走登录）
  2) 生成代码（必须使用 `TestCodeGenerator.generate_all(page_info)`，生成 Page Object + tests + test-data）
  3) 执行测试（至少跑 P0/P1/P2；输出 pytest 结果；必要时生成/打开 Allure 报告）

## 只允许 smoke 的条件（强制）
- 只有当用户明确包含这些关键词之一时，才允许只生成 1 条 smoke 用例：
  - “smoke” / “冒烟” / “快速验证” / “只测能不能打开”

## 对 /admin 路由的约束（强制）
- `/admin/*` 页面默认需要登录态：生成的测试必须使用 `auth_page`（或等价的 storage_state context）来执行。
- 生成的 P0「页面加载」用例必须断言：不会被重定向到 `/auth/login` 或 `/Account/Login`。



## ⚙️ 推荐默认环境变量（强制遵守的默认值）

> 目标：默认跑出来就是“快 + 稳 + 报告不吵”。需要更细证据时再开开关。

- **截图范围**：`FULL_PAGE_SHOT=0`（默认视口；需要全页审计再开 1）
- **Allure 降噪**：
  - `ALLURE_SHOW_BACKEND=0`（默认不展示后端/回滚诊断）
  - `ALLURE_SHOW_META=0`（默认不展示规则快照/来源等元信息）
  - `ALLURE_SHOW_DEBUG=0`（默认不展示 debug 截图/提示，如 baseline/teardown 截图）
- **Toast 稳定性**：
  - `SUCCESS_TOAST_WAIT_MS=8000`
  - `TOAST_SETTLE_MS=8000`
- **并发稳定性**：并发跑前建议开
  - `PRECHECK_ACCOUNTS=1`（账号池预检）
  - `REUSE_LOGIN=1`（复用登录态）
- **提速开关（谨慎使用）**：`FAST=0`（默认关闭；仅本地快速回归时开 1）

## Allure 报告卫生（强制，避免“报告两套/历史混入”）
- 只要用户触发“测试某页面/URL/运行测试”，在跑 pytest **之前必须先清理旧数据**（除非用户明确说“保留历史趋势/history”）：  
  - 删除：`allure-results/`、`allure-report/`、`screenshots/`  
  - 重建：`allure-results/`、`screenshots/`
- 测试完成后必须执行：  
  - `allure generate allure-results -o allure-report --clean`
- 打开报告必须使用 **HTTP**：推荐静态服务（更稳），备选 allure open：  
  - `python3 -m http.server 59717 --bind 127.0.0.1 --directory "allure-report"` → `http://127.0.0.1:59717/`  
  - 或：`allure open allure-report -h 127.0.0.1 -p 0`（后台运行，并把输出的 URL 回显给用户）

## 执行时序（强制）
- 禁止并行触发“生成代码”和“运行 pytest”，必须确保文件生成落盘后再运行测试，避免 `file not found` 竞态。