---
alwaysApply: true
---

# ⭐ 页面分析与代码生成流程（核心）

当用户说"测试 xxx 页面"时，**必须使用双重分析**：

## 双重分析策略

**1. GitHub 代码分析** - 了解业务逻辑、验证规则、API 接口  
**2. Playwright MCP 分析** - 获取实际渲染的元素、可访问性信息、交互状态

两种分析结果**互补**，生成更准确的测试用例。

---

## Step 1: 读取项目配置

```python
# 读取 config/project.yaml 获取仓库信息
repositories:
  frontend:
    url: "https://github.com/owner/frontend"
  backend:
    url: "https://github.com/owner/backend"
```

## Step 2: 根据页面 URL 推断代码位置

| 页面 URL | 可能的前端代码位置 |
|----------|-------------------|
| `/login` | `src/pages/login/`, `src/views/Login.tsx` |
| `/admin/profile` | `src/pages/admin/profile/`, `src/views/Profile/` |
| `/admin/profile/change-password` | `src/pages/admin/profile/ChangePassword.tsx` |
| `/orders` | `src/pages/orders/`, `src/views/Orders/` |
| `/products/:id` | `src/pages/products/[id].tsx`, `src/views/ProductDetail/` |

**常见前端项目结构：**
- React: `src/pages/`, `src/views/`, `src/components/`
- Vue: `src/views/`, `src/pages/`, `src/components/`
- Next.js: `pages/`, `app/`

## Step 3A: 使用 GitHub 代码分析

**提取信息**:
- 表单字段定义
- 验证规则（正则、长度限制）
- API 接口（请求方法、参数、响应）
- 业务逻辑（条件判断、流程分支）

## Step 3B: 使用 Playwright MCP 分析页面

**智能服务检查与等待**:
1. 检查服务状态
   - 如果服务已启动 → 直接使用 MCP 分析
   - 如果服务未启动 → 提示用户并等待（最多60秒）
   - 服务启动后 → 自动使用 MCP 重新分析

**如果服务未启动**:
- 使用标准页面结构生成代码（基于 URL 推断）
- 提示用户启动服务后重新分析
- 服务启动后可以自动更新代码

## Step 4: 合并分析结果

**整合两种分析**:
1. 使用 MCP 分析结果作为基础（实际元素）
2. 使用 GitHub 分析结果丰富信息（业务逻辑、验证规则）
3. 合并相同元素，补充缺失信息
4. 生成完整的 PageInfo 对象

## Step 5: 生成测试代码

基于分析结果生成覆盖以下场景的测试：

| 优先级 | 测试类型 | 来源 |
|--------|----------|------|
| P0 | 核心功能测试 | 主要业务流程 |
| P0 | 必填字段验证 | 表单验证规则 |
| P1 | 边界值测试 | 长度限制、数值范围 |
| P1 | 格式验证测试 | 正则表达式规则 |
| P1 | API 错误处理 | 接口异常场景 |
| P2 | UI 状态测试 | 加载、禁用、高亮 |

---

**下一步**：测试代码生成完成后，执行 `workflow/test-execution.md` 中的自动测试流程。
