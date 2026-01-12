"""
Eval 框架配置
支持多种 LLM 提供商，通过环境变量配置

使用方法:
    # 方式 1：环境变量
    export EVAL_LLM_PROVIDER=deepseek
    export DEEPSEEK_API_KEY=sk-xxx
    
    # 方式 2：.env 文件
    # 在项目根目录创建 .env 文件
    
    # 方式 3：代码中直接配置
    from eval.config import EvalConfig
    config = EvalConfig(provider="deepseek", api_key="sk-xxx")
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class LLMProvider(Enum):
    """支持的 LLM 提供商"""
    DEEPSEEK = "deepseek"      # 性价比之王
    ZHIPU = "zhipu"            # 智谱 GLM
    OPENAI = "openai"          # OpenAI GPT
    OLLAMA = "ollama"          # 本地 Ollama（免费）


# 各提供商的配置
PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",  # 便宜
        "env_key": "ZHIPU_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:7b",
        "env_key": None,  # 不需要 key
    },
}


@dataclass
class EvalConfig:
    """
    Eval 配置类
    
    优先级：代码参数 > 环境变量 > 默认值
    """
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    threshold: float = 0.7
    
    # 评估维度权重
    weights: Dict[str, float] = field(default_factory=lambda: {
        "logic": 0.25,          # 逻辑正确性
        "evidence": 0.25,       # 证据充分性
        "accuracy": 0.20,       # 事实准确性
        "completeness": 0.15,   # 完整性
        "insight": 0.15,        # 洞察力
    })
    
    def __post_init__(self):
        """初始化后处理：从环境变量读取配置"""
        # 从环境变量读取 provider（优先级：代码参数 > 环境变量 > 默认值）
        if not self.provider:
            self.provider = os.getenv("EVAL_LLM_PROVIDER", "deepseek")
        
        # 获取提供商配置
        provider_config = PROVIDER_CONFIGS.get(self.provider, {})
        
        # 设置 base_url
        if not self.base_url:
            self.base_url = provider_config.get("base_url")
        
        # 设置 model
        if not self.model:
            self.model = os.getenv("EVAL_LLM_MODEL") or provider_config.get("default_model")
        
        # 设置 api_key
        if not self.api_key:
            env_key = provider_config.get("env_key")
            if env_key:
                self.api_key = os.getenv(env_key)
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        if self.provider == "ollama":
            return True  # Ollama 不需要 key
        return bool(self.api_key and self.base_url and self.model)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "threshold": self.threshold,
            "has_api_key": bool(self.api_key),
        }


# 默认配置实例
def get_default_config() -> EvalConfig:
    """获取默认配置（从环境变量）"""
    return EvalConfig()

