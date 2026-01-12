"""
轻量级 LLM 客户端
使用原生 requests，不依赖 openai 包

解决架构兼容性问题（如 pydantic_core arm64/x86_64 冲突）
"""

import json
import requests
from typing import Dict, Any, Optional, List


class LLMClient:
    """
    轻量级 LLM 客户端（原生 requests 实现）
    
    支持所有 OpenAI 兼容 API：
    - DeepSeek
    - 智谱 GLM
    - OpenAI
    - Ollama
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 60
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            messages: [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大输出 tokens
        
        Returns:
            完整的 API 响应
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_content(self, response: Dict[str, Any]) -> str:
        """从响应中提取内容"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""


# ============================================================
# 预配置的客户端工厂函数
# ============================================================

def create_deepseek_client(api_key: str, model: str = "deepseek-chat") -> LLMClient:
    """创建 DeepSeek 客户端"""
    return LLMClient(
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
        model=model
    )


def create_zhipu_client(api_key: str, model: str = "glm-4-flash") -> LLMClient:
    """创建智谱客户端"""
    return LLMClient(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=api_key,
        model=model
    )


def create_openai_client(api_key: str, model: str = "gpt-4o-mini") -> LLMClient:
    """创建 OpenAI 客户端"""
    return LLMClient(
        base_url="https://api.openai.com/v1",
        api_key=api_key,
        model=model
    )


def create_ollama_client(model: str = "qwen2.5:7b") -> LLMClient:
    """创建 Ollama 客户端（本地）"""
    return LLMClient(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Ollama 不需要真正的 key
        model=model
    )

