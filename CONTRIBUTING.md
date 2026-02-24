# 贡献指南

感谢你对本项目的兴趣！

---

## 如何贡献

### 1. Fork 仓库

```bash
git clone https://github.com/<your-username>/playwright-test-scaffold.git
cd playwright-test-scaffold
```

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 3. 编写代码

遵循项目的代码规范（见 `README.md` 与 `docs/architecture.md`）：

- 文件不超过 400 行
- 函数不超过 20 行
- 清晰的命名
- 必要的注释

### 4. 运行测试

```bash
# 确保测试通过
make test TEST_TARGET=tests/

# 检查代码风格
make lint
```

### 5. 提交 PR

```bash
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
```

---

## 代码规范

### Python 代码

- 使用 `ruff` 或 `black` 格式化
- 类型注解
- docstring

### 测试代码

- Page Object 模式
- 关键步骤截图
- 数据隔离

### 文档

- 中文注释
- Markdown 格式
- 更新架构文档

---

## 提交规范

使用 Conventional Commits：

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
refactor: 重构
test: 测试
chore: 其他
```

---

## 问题反馈

- 提交 Issue 描述问题
- 附上复现步骤
- 附上日志或截图

---

**Happy Contributing! 🎉**

