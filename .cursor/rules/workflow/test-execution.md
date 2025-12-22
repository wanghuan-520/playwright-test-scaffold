---
alwaysApply: true
---

# 🚀 自动测试执行流程

**测试代码生成完成后，自动执行以下流程：**

## 执行流程

```
0. 清理旧的测试数据（必须）⭐
   ├─ 删除 allure-results/（旧的测试结果数据）
   ├─ 删除 allure-report/（旧的 HTML 报告）
   ├─ 删除 screenshots/（旧的测试截图）
   └─ 确保每次测试都是干净的开始

1. 检查服务状态
   ├─ 前端服务（https://localhost:3000）
   └─ 后端服务（https://localhost:44320）
   
2. 运行 pytest
   └─ pytest tests/test_<page_name>.py -v
   
3. 收集测试结果
   
4. 生成 Allure 报告
   
5. 自动打开报告（必须）
   ├─ allure generate allure-results -o allure-report --clean
   └─ **优先用静态 HTTP 服务打开**（更稳，不依赖 allure open/serve 子进程）：
      - python3 -m http.server 59717 --bind 127.0.0.1 --directory "allure-report"
      - 打开：http://127.0.0.1:59717/

   备选（可用但不如静态服务稳）：
   - allure open allure-report  （HTTP 打开，避免 file:// 一直 Loading）
   
6. 反馈测试结果摘要
```

## ✅ Allure 报告打开强制规则（必须遵守）

- **强烈推荐**：优先使用 `python3 -m http.server --directory allure-report` 提供静态服务（本项目在并发/进程资源紧张时，allure open/serve 偶发启动失败）。
- 若使用静态服务：建议固定端口（例如 59717），并在启动前杀掉旧进程（避免端口占用）。


- **必须**: 最终打开方式必须是 **HTTP**（二选一即可）：
  - `python3 -m http.server --directory allure-report`（推荐，最稳）
  - `allure open allure-report`（可用）
- **禁止**: 使用 `open allure-report/index.html`（file:// 方式，可能导致 Allure 一直 Loading）

## 🧠 执行稳定性规则（避免 ABP lockout）

- **必须**: 大规模用例集（P1/P2/security）优先使用 `auth_page`（基于 `storage_state`）复用登录态
- **禁止**: 在每条用例内重复走 `/auth/login` → `/Account/Login`
- **建议**: 示例用例必须使用 `example` 标记，避免混入 P0/P1/P2/security 回归集合

## 自动化规则

**何时自动运行测试**：
- ✅ 用户说"帮我测试 xxx 页面"（生成代码后自动运行）
- ✅ 用户说"测试 /admin/profile/change-password"（生成代码后自动运行）
- ❌ 用户说"生成 xxx 页面的测试代码"（只生成，不运行）
- ❌ 用户说"帮我写测试"（只生成，不运行）

**触发自动运行的关键词**：
- "测试 xxx 页面"
- "帮我测试"
- "运行测试"
- "执行测试"

## 实现细节

```python
# 0. 清理旧的测试数据（必须）⭐
def clean_old_test_data():
    """清理旧的测试数据，确保每次测试都是干净的开始"""
    import shutil
    import os
    
    # 清理 allure-results
    if os.path.exists("allure-results"):
        shutil.rmtree("allure-results")
        print("✅ 已清理旧的测试结果: allure-results/")
    
    # 清理 allure-report
    if os.path.exists("allure-report"):
        shutil.rmtree("allure-report")
        print("✅ 已清理旧的测试报告: allure-report/")
    
    # 清理 screenshots
    if os.path.exists("screenshots"):
        shutil.rmtree("screenshots")
        print("✅ 已清理旧的测试截图: screenshots/")
    
    # 重新创建必要的目录
    os.makedirs("allure-results", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    print("✅ 已创建新的测试数据目录")

# 1. 检查服务状态
def check_services():
    """检查前端和后端服务是否启动"""
    frontend_url = "https://localhost:3000"
    backend_url = "https://localhost:44320"
    
    frontend_status = shell("curl -k {frontend_url} -I")
    backend_status = shell("curl -k {backend_url}/api/health -I")
    
    return frontend_status.success and backend_status.success

# 2. 运行测试
def run_tests(test_file: str):
    """运行生成的测试文件"""
    # pytest.ini 已配置 --alluredir=allure-results
    cmd = f"pytest {test_file} -v"
    result = shell(cmd, timeout=180000)  # 3分钟超时
    return parse_pytest_output(result.output)

# 3. 生成并自动打开 Allure 报告
def open_allure_report():
    """生成 Allure 报告并自动在浏览器中打开"""
    # 先生成静态报告
    shell("allure generate allure-results -o allure-report --clean", timeout=60000)
    # 使用 HTTP 打开（Allure 内置 WebServer），避免浏览器 file:// 策略导致一直 Loading
    result = shell("allure open allure-report -h 127.0.0.1 -p 0", is_background=True)
    return "allure open allure-report"
```

## 清理机制说明

### ⚠️ 为什么要清理旧数据？

1. **避免数据混淆**
   - 旧的测试结果、截图会和新的混在一起
   - Allure 会显示所有历史数据，导致报告不准确

2. **确保结果准确**
   - 每次测试都是独立的、干净的
   - 报告和截图只显示本次测试的结果

3. **避免磁盘空间浪费**
   - 测试数据会不断累积
   - 定期清理节省空间

4. **便于问题定位**
   - 截图只包含本次测试
   - 不会被历史截图干扰

### 清理的内容

| 目录 | 内容 | 清理方式 | 原因 |
|------|------|---------|------|
| `allure-results/` | 测试结果数据（JSON） | 完全删除 + 重建 ✅ | 每次重新生成 |
| `allure-report/` | HTML 报告 | 完全删除 ✅ | 每次重新生成 |
| `screenshots/` | 测试截图 | 完全删除 + 重建 ✅ | 每次重新生成 |

**所有测试数据都会自动清理，确保每次测试都是全新的开始。** ✨

### 清理时机

```
用户触发测试
  ↓
Step 0: 清理旧数据 ← ⭐ 第一步
  ├─ 删除 allure-results/
  ├─ 删除 allure-report/
  ├─ 删除 screenshots/
  ├─ 重建 allure-results/
  └─ 重建 screenshots/
  ↓
Step 1: 检查服务
  ↓
Step 2: 运行 pytest
  ↓
...
```

## 结果反馈格式

## 常见问题

### Allure 报告用 file:// 打开一直 Loading

- **原因**: 浏览器安全策略可能阻止 Allure 在 file:// 下加载报告数据。
- **解决**: 使用 HTTP 打开：`allure open allure-report`（推荐）或 `allure serve allure-results`。


**全部通过时**：
```
🧹 清理旧测试数据...
✅ 已清理旧的测试结果: allure-results/
✅ 已清理旧的测试报告: allure-report/
✅ 已清理旧的测试截图: screenshots/
✅ 已创建新的测试数据目录

✅ 测试完成！所有测试通过！

📊 测试结果概览:
- 总测试数: 13
- ✅ 通过: 13 (100%)

⏱️  执行时间: 45.3 秒

📝 Allure 报告已自动打开: http://localhost:xxxxx
   → 浏览器会自动弹出报告页面
   → 可查看详细的测试步骤、截图和统计
```

**部分失败时**：
```
🧹 清理旧测试数据...
✅ 已清理旧的测试结果: allure-results/
✅ 已清理旧的测试报告: allure-report/
✅ 已清理旧的测试截图: screenshots/
✅ 已创建新的测试数据目录

⚠️ 测试完成！部分测试失败

📊 测试结果概览:
- 总测试数: 13
- ✅ 通过: 11 (85%)
- ❌ 失败: 2 (15%)

❌ 失败的测试详情:
1. test_p1_password_too_short
   └─ 原因: 后端未启用 RequiredLength 验证规则
   └─ 建议: 检查后端 ABP 配置或调整测试断言

📝 Allure 报告已自动打开: http://localhost:xxxxx
   → 点击失败的测试查看完整日志和截图
```

## 手动清理命令（可选）

如果需要手动清理，可以执行：

```bash
# 清理所有测试相关数据
rm -rf allure-results/ allure-report/ screenshots/

# 或使用 Python 脚本
python -c "import shutil; shutil.rmtree('allure-results', ignore_errors=True); shutil.rmtree('allure-report', ignore_errors=True); shutil.rmtree('screenshots', ignore_errors=True); print('✅ 清理完成')"
```

---

**核心原则：每次测试都是干净的开始，所有数据只反映本次测试结果。** ✨


# ✅ 闭环执行（强制）

> 目标：当用例很多、失败很多时，仍能**快速收敛**；并且 Allure 报告永远只反映“本次运行”。

## 0) 执行前清理（必须）

- **默认必须清理**（每次 pytest run 视为一次独立 run，不允许混入历史）：
  - `allure-results/`
  - `allure-report/`
  - `screenshots/`

- **例外（仅当你明确需要 Allure 趋势/history）**：允许保留 `allure-results/history/`。
  - 触发方式：设置环境变量 `KEEP_ALLURE_HISTORY=1`
  - 除 `history/` 外，其它仍必须清理

## 1) 失败时证据自动采集（必须）

任何测试失败，都必须自动采集并在 Allure 中可见（否则视为“不可诊断失败”）：

- **screenshot**：失败时至少 1 张全页截图
- **console logs**：至少包含失败用例期间的 console 输出
- **requestfailed**：至少包含失败用例期间的 requestfailed 列表（method/url/error）
- **trace**：对需要登录态的用例（默认 `auth_page`）必须生成 Playwright trace（zip）并附加

## 2) 批量失败的收敛策略（必须遵守的执行顺序）

当失败数量较多时，禁止逐条“补断言/改 sleep”式修补。
必须按以下顺序收敛：

1. **P0 优先**：先跑 `-m P0` 止血
2. **分型**：把失败归类为 INFRA / AUTH-DATA / SELECTOR / RULE-DRIFT / RACE
3. **修根因**：优先修框架/公共 helper/选择器策略/规则推导，不在单条用例里打补丁
4. **只重跑失败**：`--lf` 或 `-k`，直到失败归零