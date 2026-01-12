# Eval 框架 LLM 配置指南

## 快速开始

### 方式 1：环境变量（推荐）

```bash
# 使用 DeepSeek（性价比之王）
export EVAL_LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-your-key

# 或使用智谱
export EVAL_LLM_PROVIDER=zhipu
export ZHIPU_API_KEY=your-zhipu-key

# 或使用 OpenAI
export EVAL_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key

# 或使用 Ollama（本地，免费）
export EVAL_LLM_PROVIDER=ollama
# 不需要 API Key
```

### 方式 2：代码中配置

```python
from eval import EvalConfig, EvalPipeline

config = EvalConfig(
    provider="deepseek",
    api_key="sk-your-key",
    model="deepseek-chat",  # 可选
)

pipeline = EvalPipeline(config)
result = pipeline.run(ai_output, context="研究方向")
```

### 方式 3：.env 文件

在项目根目录创建 `.env` 文件：

```
EVAL_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
```

然后安装 python-dotenv：

```bash
pip install python-dotenv
```

在代码中加载：

```python
from dotenv import load_dotenv
load_dotenv()

from eval import full_eval
result = full_eval(ai_output)
```

---

## 支持的 LLM 提供商

| 提供商 | 价格 | 推荐模型 | 说明 |
|-------|------|---------|------|
| **DeepSeek** | ¥0.001/千tokens | deepseek-chat | 🏆 性价比之王 |
| **智谱** | ¥0.0001/千tokens | glm-4-flash | 超便宜 |
| **OpenAI** | $3/百万tokens | gpt-4o-mini | 综合最强 |
| **Ollama** | 免费 | qwen2.5:7b | 需要本地 GPU |

---

## 获取 API Key

### DeepSeek（推荐）

1. 访问 https://platform.deepseek.com/
2. 注册账号
3. 在 API Keys 页面创建 Key
4. 新用户有免费额度

### 智谱 GLM

1. 访问 https://open.bigmodel.cn/
2. 注册账号
3. 在 API 密钥页面创建 Key
4. 新用户有免费额度

### Ollama（本地部署，完全免费）

```bash
# 安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull qwen2.5:7b

# 运行
ollama serve
```

---

## 使用示例

### 1. 快速评估（只用规则，免费）

```python
from eval import is_quality_ok

if is_quality_ok(ai_output):
    print("基本合格")
```

### 2. 完整评估（规则 + LLM）

```python
from eval import full_eval

result = full_eval(
    text=ai_output,
    context="研究方向：探索 LLM 在科研中的应用"
)

print(f"综合得分: {result['overall_score']}")
print(f"是否通过: {result['overall_passed']}")
```

### 3. 理论验证（专门评估推理正确性）

```python
from eval import LLMEvaluator

evaluator = LLMEvaluator()
result = evaluator.evaluate_theory(
    theory="结论：X 导致 Y",
    premises=["前提1", "前提2", "前提3"],
    expected_conclusion="预期结论（可选）"
)
```

### 4. 批量评估

```python
from eval import EvalPipeline

pipeline = EvalPipeline()
report = pipeline.run_batch([
    {"text": output1, "context": "问题1"},
    {"text": output2, "context": "问题2"},
])

print(f"通过率: {report['pass_rate']}")
print(f"平均分: {report['avg_score']}")
```

---

## 成本估算

假设每次评估 2000 tokens：

| 提供商 | 100 次/天 | 月成本 |
|-------|----------|--------|
| DeepSeek | ¥0.2 | ¥6 |
| 智谱 GLM-4-Flash | ¥0.02 | ¥0.6 |
| OpenAI GPT-4o-mini | ¥2 | ¥60 |
| Ollama | 免费 | ¥0 |

