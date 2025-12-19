# 📋 配置文件说明

## 配置文件结构

```
config/
├── project.yaml               ← 实际配置（不提交到 Git）⚠️
└── project.yaml.example       ← 配置模板（提交到 Git）✅
```

## 🚀 快速开始

### 1. 复制模板文件

```bash
# 复制配置模板
cp config/project.yaml.example config/project.yaml
```

### 2. 修改配置

编辑 `config/project.yaml`，填写你的项目信息：

#### 项目基本信息
```yaml
project:
  name: "你的项目名称"
  description: "项目描述"
  version: "1.0.0"
```

#### 代码仓库路径
```yaml
repositories:
  frontend:
    local_path: "/path/to/your/frontend"   # 修改为你的前端项目路径
    url: "https://github.com/owner/repo"    # 可选：GitHub URL
  
  backend:
    local_path: "/path/to/your/backend"    # 修改为你的后端项目路径
```

#### 服务地址
```yaml
environments:
  dev:
    frontend:
      url: "https://localhost:3000"        # 修改为你的前端 URL
    backend:
      url: "https://localhost:44320"       # 修改为你的后端 URL
```

#### 服务启动配置
```yaml
service_startup:
  frontend:
    command: "npm run dev"                 # 修改为你的启动命令
    cwd: "/path/to/your/frontend"          # 修改为你的前端项目路径
  
  backend:
    command: "dotnet run"                  # 修改为你的启动命令
    cwd: "/path/to/your/backend"           # 修改为你的后端项目路径
```

## ⚠️ 重要说明

### 不要提交到 Git

`config/project.yaml` 包含本地路径等敏感信息，已添加到 `.gitignore`，**不会被提交到 Git**。

### 配置文件的区别

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `project.yaml` | 实际配置（包含真实路径） | ❌ 不提交 |
| `project.yaml.example` | 配置模板（示例路径） | ✅ 提交 |

## 📝 配置项说明

### repositories（代码仓库）

- `local_path`: 本地代码路径（用于 AI 代码分析）
- `url`: GitHub URL（可选，用于远程代码分析）
- `tech_stack`: 技术栈信息（帮助 AI 理解项目）

### environments（服务环境）

- `dev`: 开发环境
- `staging`: 预发布环境
- `production`: 生产环境

每个环境包含：
- `frontend.url`: 前端服务地址
- `backend.url`: 后端服务地址
- `health_check`: 健康检查路径

### service_startup（服务启动）

- `enabled`: 是否启用自动启动
- `auto_start`: 检测到服务未启动时是否自动启动
- `command`: 启动命令
- `cwd`: 工作目录（项目路径）
- `timeout`: 启动超时时间（秒）

### test_data（测试数据）

- `accounts.path`: 测试账号池文件路径

## 🔧 高级配置

### 浏览器配置

```yaml
browser:
  headless: true          # 无头模式
  slow_mo: 0              # 操作延迟（毫秒）
  timeout: 30000          # 默认超时（毫秒）
  type: "chromium"        # 浏览器类型
```

### 测试执行配置

```yaml
test:
  retry_count: 2                   # 失败重试次数
  screenshot_on_failure: true      # 失败时截图
  parallel_workers: "auto"         # 并行 worker 数量
```

## 💡 最佳实践

1. **本地开发**
   - 使用 `config/project.yaml`（不提交）
   - 包含真实的本地路径

2. **团队协作**
   - 提交 `config/project.yaml.example`
   - 团队成员复制并修改为自己的路径

3. **CI/CD**
   - 使用环境变量或配置管理工具
   - 动态生成 `project.yaml`

---

**配置完成后即可开始使用！** ✨
