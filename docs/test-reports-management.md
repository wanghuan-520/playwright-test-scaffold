# 测试报告管理规范

## 📁 标准目录结构

```
playwright-test-scaffold/
├── allure-results/      ← 原始测试结果（pytest 输出，JSON 格式）
├── allure-report/       ← 最新测试报告（Allure 生成的 HTML）
├── screenshots/         ← 测试截图（失败/关键步骤）
└── reports/            ← pytest 日志文件
```

## 🚫 禁止的混乱模式

❌ **不要手动创建这些文件夹**：
- `allure-report-admin-profile/`
- `allure-report-new/`
- `allure-results-fix/`
- 任何 `allure-*-*` 格式的文件夹

## ✅ 标准工作流

### 1. 运行测试

```bash
# 运行所有测试
make test

# 运行特定功能测试
make test TEST_TARGET=tests/admin/profile

# 运行 P0 级别测试
make test-p0

# 运行特定功能的 P0 测试
make test-p0 TEST_TARGET=tests/admin/profile
```

**输出位置**：`allure-results/`

### 2. 生成报告

```bash
make report
```

**输出位置**：`allure-report/`

### 3. 查看报告

```bash
make serve
```

**浏览器访问**：http://127.0.0.1:59717

### 4. 清理报告

```bash
# 清理所有测试报告
make clean

# 只清理缓存
make clean-cache
```

## 🎯 报告生命周期

```
运行测试 → allure-results/ → 生成报告 → allure-report/ → 查看 → 清理
   ↓                            ↓
自动同步到 .allure-cache/    持久化历史数据
```

## 🔄 历史数据管理

**Allure 自动管理历史**：
- `.allure-cache/` - 保存历史趋势数据
- 每次 `make report` 会自动合并历史数据
- 不需要手动管理多个报告文件夹

## 🧹 清理混乱结构

如果你的项目中有多个 `allure-report-*` 文件夹：

```bash
# 运行清理脚本（会提示是否备份）
./scripts/cleanup_allure_folders.sh
```

## 📝 最佳实践

### ✅ 推荐做法

1. **始终用 Makefile 运行测试**
   ```bash
   make test TEST_TARGET=tests/admin
   ```

2. **报告查看完后及时清理**
   ```bash
   make clean
   ```

3. **需要保存报告时，用浏览器"另存为"**
   - 在 `http://127.0.0.1:59717` 按 `Ctrl+S`
   - 保存到 `docs/test-reports/YYYYMMDD-feature-name/`

4. **长期存档用 Allure 导出功能**
   ```bash
   # 导出完整报告到指定位置
   allure generate allure-results -o archived-reports/2026-01-05-release-v1.0
   ```

### ❌ 避免做法

1. **不要手动创建报告文件夹**
   ```bash
   # ❌ 错误
   pytest --alluredir=allure-results-fix
   allure generate allure-results -o allure-report-admin-profile
   ```

2. **不要在项目根目录保存多个报告**
   - 会导致混乱
   - 会占用大量磁盘空间
   - 会被 git 忽略，无法共享

3. **不要手动修改 allure-results/**
   - 这是 pytest 自动生成的
   - 手动修改会破坏报告一致性

## 🔍 故障排查

### 问题：报告没有历史趋势

**原因**：`.allure-cache/` 被删除

**解决**：
```bash
# 重新运行测试，历史会慢慢积累
make clean-cache  # 清理损坏的缓存
make test         # 开始新的历史记录
```

### 问题：报告显示旧数据

**原因**：`allure-results/` 没有清理

**解决**：
```bash
make clean  # 清理所有旧数据
make test   # 生成新数据
make report # 生成新报告
```

### 问题：多个 allure-report-* 文件夹

**原因**：手动运行了带自定义输出目录的命令

**解决**：
```bash
./scripts/cleanup_allure_folders.sh  # 运行清理脚本
```

## 📊 .gitignore 配置

已配置忽略所有测试报告文件夹：

```gitignore
# Test Reports
allure-results/
allure-results-*/
allure-report/
allure-report-*/
reports/
screenshots/
```

**意味着**：
- ✅ 本地测试报告不会提交到 git
- ✅ 每个开发者有自己的报告
- ✅ CI/CD 可以生成独立的报告

## 🎓 宪法原则

**简化和文件组织**：
> "认知负荷是敌人。保持模块小型、专注、可导航。"

- 只保留 2 个标准文件夹
- 清晰的命名约定
- 自动化的生命周期管理
- 避免手动创建临时文件夹

---

**维护者**：遵循此规范，保持项目整洁！
**新成员**：遵循此规范，快速上手！

