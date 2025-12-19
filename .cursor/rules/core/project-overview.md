---
alwaysApply: true
---

# 项目核心定位与架构

## 项目定位

这是一个 **AI 驱动的 Playwright + Python 自动化测试脚手架**，通过自然语言对话生成：
- Page Object 页面对象  
- Test Cases 测试用例
- Test Data 测试数据
- Test Reports 测试报告（Allure HTML）

**使用方式：只通过 AI 对话交互，无需命令行。**

## 🚀 核心测试流程

**完整自动化工作流**：
```
用户请求 
  ↓
页面分析（双重分析：代码 + 实时页面）
  ↓
生成测试代码（Page Object + Test Cases）
  ↓
自动运行测试（pytest + Allure）
  ↓
自动打开报告（浏览器自动弹出）✨
  ↓
反馈结果摘要（通过/失败/建议）
```

**触发指令**：
- "帮我测试 xxx 页面"
- "生成 xxx 功能的测试"
- "测试 /admin/profile/change-password"

**核心特点**：
- ✅ 完全自动化：从分析到报告，一气呵成
- ✅ 无外部依赖：完全本地执行
- ✅ 企业级质量：Allure 报告 + 完整截图
- ✅ 智能数据管理：独立账号 + 自动清洗
- ✅ ABP 规则覆盖：6 个标准密码验证规则

## ⚠️ 代码生成前必读（Critical）

**在生成任何 Page Object 或 Test Case 代码之前，必须执行以下步骤：**

```
必读文件（按顺序）：
1. config/project.yaml                    → 项目配置（仓库/服务/数据）
2. generators/page_object_generator.py    → Page Object 生成模板
3. generators/test_case_generator.py      → 测试用例生成模板
4. generators/test_case_templates.py      → 测试用例模板参考
5. utils/logger.py                        → Logger 使用方式
```

## 测试优先级

| 标记 | 含义 | 场景 |
|------|------|------|
| P0 | 核心功能 | 主流程、关键路径 |
| P1 | 重要功能 | 输入验证、边界值 |
| P2 | 一般功能 | UI样式、可访问性 |

## 代码风格

- 中文注释，英文代码
- 使用 ASCII 风格分块注释
- 文件不超过 400 行
- 函数职责单一
