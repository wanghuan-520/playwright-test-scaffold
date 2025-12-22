---
alwaysApply: true
---

# ⭐ 页面分析与代码生成流程（核心）

> 这是一个“完整可复制”的 tmp 版本：用于手动覆盖 `.cursor/rules/workflow/analysis-and-generation.md`。

当用户说"测试 xxx 页面"时，**必须使用双重分析**，并且**首次生成全量用例就必须参照前后端代码推导规则**（禁止凭猜）。

## 双重分析策略

**1. 前后端代码分析（静态）** - 了解业务逻辑、验证规则、API 接口  
**2. Playwright MCP 分析（动态）** - 获取实际渲染的元素、可访问性信息、交互状态

两种分析结果**互补**，生成更准确的测试用例。

---

## Step 1: 读取项目配置

必须读取 `config/project.yaml`：

- `repositories.frontend.local_path`（优先，本地代码分析的事实来源）
- `repositories.backend.local_path`（优先）
- 若 local_path 不存在/不可用，才退化为 GitHub URL / 纯动态分析

---

## Step 2: 根据页面 URL 推断代码位置

| 页面 URL | 可能的前端代码位置 |
|----------|-------------------|
| `/login` | `src/pages/login/`, `src/views/Login.tsx` |
| `/admin/profile` | `src/app/admin/profile/page.tsx`（Next.js App Router） / `src/pages/admin/profile/` / `src/views/Profile/` |
| `/admin/profile/change-password` | `src/app/admin/profile/change-password/page.tsx`（Next.js App Router） / `src/pages/admin/profile/ChangePassword.tsx` |
| `/orders` | `src/pages/orders/`, `src/views/Orders/` |
| `/products/:id` | `src/pages/products/[id].tsx`, `src/views/ProductDetail/` |

**常见前端项目结构：**
- React: `src/pages/`, `src/views/`, `src/components/`
- Vue: `src/views/`, `src/pages/`, `src/components/`
- Next.js: `pages/`, `app/`

---

## Step 3A: 前后端代码分析（强制）

> ✅ 强制：**首次生成全量用例集（P0/P1/P2/security）时就必须参照前后端代码推导字段规则**。  
> ❌ 禁止：先生成一堆骨架/数量达标，再等反馈补规则。  
> ✅ 默认：**前端 + 后端各至少一种来源**（除非确实缺失某一侧代码仓库，才允许降级，并必须在用例里写清楚“来源缺失→断言降级/skip”）。

### 前端规则来源（至少一种，默认必须读取）

- 页面入口：Next.js `src/app/**/page.tsx` / React `src/pages/**` / 组件 `src/components/**`
- 表单校验：重点读取 `react-hook-form register()` 的参数：
  - `required`
  - `maxLength/minLength`
  - `pattern`（正则）
  - `validate`（自定义业务规则）
- **HTML5 validity 必须考虑**：
  - `input type="email"` 等可能由浏览器原生校验拦截 submit
  - 对此类用例：优先断言“不会触发提交 API”，不要强绑错误文案（跨 OS/浏览器不稳定）

### 后端规则来源（至少一种，默认必须读取）

- ABP DTO/Attribute（`[Required]`/`[StringLength]`/`[EmailAddress]` 等）
- OpenAPI/SDK：`src/client/types.gen.ts` / `src/client/sdk.gen.ts` 的 DTO 与接口定义（例如 `/api/account/my-profile`）

### 必须输出（否则视为“未完成分析”）

- 必须形成“字段规则表”（可以在测试文件注释或 Allure 里体现）：
  - 字段名/选择器
  - required/optional
  - min/max/regex/pattern/HTML5 type
  - 对应的来源文件路径（前端/后端）
- 测试断言必须能追溯来源（至少在用例旁边用 `# Source:` 注释标注到具体文件/规则）

---

## ✅ 强制新增：ABP 规则拉取 + 前后端一致性用例（本次踩坑固化）

当页面涉及 ABP 后端表单提交（例如 `PUT /api/account/my-profile`）时：

- **必须先从后端拉取规则**（至少一种）：
  - OpenAPI/Swagger（优先）或 DTO attributes（若有后端代码）
- **必须生成 1 条规则快照用例**：
  - `*_abp_rules_snapshot`：把字段 required/maxLength/minLength/pattern 作为 Allure 附件挂出（审计/对齐/排查 drift）
- **必须生成一致性用例（核心）**：
  - 对每个“后端会拒绝”的输入（required 为空、max+1、pattern 明显非法）：
    - 前端必须拦截：断言不发写请求（避免“前端放行→后端报错”）
    - 后端也拒绝：同一输入直连 API 断言 4xx + 可诊断错误体

> 目标：永远不出现“前端放行 → 调后端才报错”。

---

## Step 3B: Playwright MCP 分析页面（动态）

**智能服务检查与等待**:
1. 检查服务状态
   - 如果服务已启动 → 直接使用 MCP 分析
   - 如果服务未启动 → 提示用户并等待（最多60秒）
   - 服务启动后 → 自动使用 MCP 重新分析

**如果服务未启动**:
- 使用标准页面结构生成代码（基于 URL 推断）
- 提示用户启动服务后重新分析
- 服务启动后可以自动更新代码

---

## Step 4: 合并分析结果

**整合两种分析**:
1. 使用 MCP 分析结果作为基础（实际元素）
2. 使用前后端代码分析结果丰富信息（业务逻辑、验证规则）
3. 合并相同元素，补充缺失信息
4. 生成完整的 PageInfo 对象 + 字段规则表

---

## Step 5: 生成测试代码（必须“字段维度”产出）

基于分析结果生成覆盖以下场景的测试（不能只生成骨架/TODO）：

| 优先级 | 必须生成的用例形态 | 来源 |
|--------|--------------------|------|
| P0 | 页面加载 | 动态 + 静态 |
| P0 | 主流程成功（happy path） | 静态 + 动态 |
| P0 | （可选）1 条“必填拦截哨兵” | 前端 register + HTML5 |
| P1 | **字段矩阵（按字段拆文件）**：有效/无效/长度/必填/空白（以 ABP 规则为准） | 前后端规则 |
| P1 | **一致性契约**：所有“应拦截”的场景必须给出可见错误证据；选取关键非法值补后端 reject 探针 | ABP/OpenAPI + UI |
| P2 | UI 最小集合：字段可见性、Tab、键盘 Tab、基础 a11y | 动态 |
| security | **按字段维度安全载荷**：每个输入框至少 XSS/SQLi；断言不弹 dialog/不跳登录/不 5xx；结束必须恢复数据 | 前后端 + 动态 |

### ✅ 字段矩阵（老兵口味）生成规则（强制）

当页面是“表单 + 保存（写接口）”形态时，默认用 **P1 字段矩阵**承担输入校验覆盖（避免 P0/P1 重复堆用例、拖慢执行）：

- **按字段拆文件**：`test_<page>_p1_<field>_matrix.py`（便于并发与精确重跑）
- **每个场景只保留 2 张关键截图**：`filled / result`
- **硬契约（必须）**：
  - 任意矩阵场景 `should_save=False` 必须设置 `require_frontend_error_evidence=True`
  - 含义：只要前端确实拦截（不发写请求），就必须能看到可检证的错误证据（validationMessage/aria-invalid/内联提示/invalid 样式）；否则用例直接红
- **后端 reject 探针（少而精）**：
  - 只对“最典型且后端必拒绝”的非法值补 `require_backend_reject=True`（例如 email 缺少 `@`）
- **禁止反模式**：
  - 禁止用“右上角注入红框”等方式伪造错误提示（只允许真实 UI 证据）
  - 禁止在 Allure 报告里展示 baseline 修正/teardown 回滚/纯断言步骤（这属于基础设施噪音）


---

## 🔐 登录/鉴权注意事项（本项目特性）

- **前端登录入口**: `/auth/login`（Next.js route handler）
- **实际登录页**: 会重定向到后端 ABP Identity 登录页（例如 `/Account/Login`），元素选择器与前端页面不同。
- **HTTPS 自签证书**: 自动化需要忽略证书错误（框架已在 browser_context_args 中启用 `ignore_https_errors=True`）。