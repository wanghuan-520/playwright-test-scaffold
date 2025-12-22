# 📚 Playwright Test Scaffold - 模块化规则系统

AI 驱动的自动化测试脚手架，通过模块化规则实现从分析到报告的全自动流程。

## 📂 架构

```
.cursor/rules/
├── project/index.md      ← 主入口（AI 自动读取）
├── core/                 ← 项目核心
├── workflow/             ← 执行流程
├── generation/           ← 代码生成
├── quality/              ← 质量保证
├── data/                 ← 数据管理
```

项目特有规则已迁移到：`docs/requirements.md`（不再维护 `.cursor/rules/project-specific/`）。

## 🚀 使用

**对 AI 说**："帮我测试 xxx 页面"  
**AI 执行**：分析 → 生成代码 → 运行测试 → 打开报告 ✨

## 📝 维护

- 修改规则：直接编辑对应模块的 .md 文件
- 查看详情：阅读 `project/index.md`

---

✨ 10 个模块 · 完全自动化 · 企业级质量
