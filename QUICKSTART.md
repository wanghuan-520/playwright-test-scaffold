# 🚀 快速开始

**3 步生成测试，5 分钟上手！**

---

## ⚡ 最简单的方式

### 在 Cursor 中输入一句话：

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：<你的页面URL>
账号：<测试账号>
密码：<测试密码>
```

### 等待 AI 完成后：

```bash
make test TEST_TARGET=tests/<你的模块>
make report && make serve
```

**就这么简单！** 🎉

---

## 📋 详细步骤

### 步骤 1：环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 安装 Allure
brew install allure  # Mac
```

### 步骤 2：配置项目

```bash
# 复制配置模板
cp config/project.yaml.example config/project.yaml
cp test-data/test_account_pool.json.example test-data/test_account_pool.json
```

编辑 `config/project.yaml`：

```yaml
project:
  name: "Your Project Name"

environments:
  default: "dev"
  dev:
    frontend:
      url: "https://localhost:3000"  # 改成你的前端地址
```

编辑 `test-data/test_account_pool.json`：

```json
{
  "test_account_pool": [
    {
      "username": "your_test_user",
      "email": "test@example.com",
      "password": "YourPassword123!",
      "initial_password": "YourPassword123!",
      "in_use": false,
      "is_locked": false
    }
  ]
}
```

### 步骤 3：生成测试

在 Cursor 中输入：

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://your-site.com/login
账号：test@example.com
密码：YourPassword123!
```

### 步骤 4：运行测试

```bash
# 运行测试
make test TEST_TARGET=tests/login

# 生成报告
make report

# 查看报告
make serve
# 浏览器打开: http://127.0.0.1:59717
```

---

## 🎯 常用命令

```bash
# 运行所有测试
make test

# 运行指定目录
make test TEST_TARGET=tests/login

# 只运行 P0 测试
make test-p0

# 清理测试结果
make clean

# 生成并查看报告
make serve
```

---

## 📁 生成的文件

```
pages/
└── xxx_page.py      # 页面对象

tests/<feature>/
├── test_xxx_p0.py   # P0 核心测试
├── test_xxx_p1.py   # P1 重要测试
└── test_xxx_security.py  # 安全测试

test-data/
└── xxx_data.json    # 测试数据
```

---

## 💡 提示

### 账号池管理

框架会自动管理测试账号：
- 每个测试用例分配独立账号
- 测试后自动释放
- 支持并行执行

建议准备 **5-10 个测试账号**。

### 修改生成的代码

生成的代码可能需要微调：
- ✅ 选择器可能需要调整
- ✅ 断言可能需要补充
- ✅ 测试数据可能需要完善

### 查看更多文档

- [框架概览](docs/framework_overview.md)
- [架构文档](docs/architecture.md)

---

## 🚨 常见问题

### Q: 测试失败怎么办？

1. 查看 Allure 报告中的截图
2. 检查选择器是否正确
3. 检查测试账号是否可用

### Q: 如何添加更多账号？

编辑 `test-data/test_account_pool.json`，添加新账号。

### Q: 如何调试测试？

```bash
# 有头模式运行
HEADLESS=false pytest tests/login -v

# 使用 Playwright Inspector
PWDEBUG=1 pytest tests/login -v
```

---

**Happy Testing! 🎭**
