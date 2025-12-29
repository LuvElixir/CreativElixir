"""
API 配置管理模块

负责 LLM API 的配置管理和调用，支持 OpenAI 兼容格式的 API。
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Generator, Optional
from pathlib import Path

from openai import OpenAI


@dataclass
class APIConfig:
    """API 配置数据类"""
    api_key: str
    base_url: str
    model_id: str
    name: str = "default"
    embedding_model: str = ""  # embedding 模型 ID
    embedding_base_url: str = ""  # embedding API 地址（可选，默认使用 base_url）
    
    def is_valid(self) -> tuple[bool, str]:
        """验证配置是否有效"""
        if not self.api_key or not self.api_key.strip():
            return False, "API Key 不能为空"
        if not self.base_url or not self.base_url.strip():
            return False, "Base URL 不能为空"
        if not self.model_id or not self.model_id.strip():
            return False, "Model ID 不能为空"
        if not self.base_url.startswith(("http://", "https://")):
            return False, "Base URL 格式错误，必须以 http:// 或 https:// 开头"
        return True, ""
    
    def has_embedding_config(self) -> bool:
        """检查是否配置了 embedding 模型"""
        return bool(self.embedding_model and self.embedding_model.strip())


# 预定义的 Embedding 模型列表
EMBEDDING_MODELS = {
    "doubao": {
        "name": "豆包 (火山引擎)",
        "models": [
            {"id": "doubao-embedding-vision-250615", "name": "doubao-embedding-vision (2048维)", "dim": 2048},
        ],
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal",
        "api_type": "doubao"
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "models": [
            {"id": "BAAI/bge-large-zh-v1.5", "name": "BGE-Large-ZH (1024维)", "dim": 1024},
            {"id": "BAAI/bge-m3", "name": "BGE-M3 (1024维)", "dim": 1024},
            {"id": "Qwen/Qwen3-Embedding-8B", "name": "Qwen3-Embedding-8B (可变维度)", "dim": 1024},
            {"id": "Qwen/Qwen3-Embedding-4B", "name": "Qwen3-Embedding-4B (可变维度)", "dim": 1024},
            {"id": "Qwen/Qwen3-Embedding-0.6B", "name": "Qwen3-Embedding-0.6B (可变维度)", "dim": 1024},
        ],
        "base_url": "https://api.siliconflow.cn/v1/embeddings",
        "api_type": "openai"
    },
    "openai": {
        "name": "OpenAI",
        "models": [
            {"id": "text-embedding-ada-002", "name": "text-embedding-ada-002 (1536维)", "dim": 1536},
            {"id": "text-embedding-3-small", "name": "text-embedding-3-small (1536维)", "dim": 1536},
            {"id": "text-embedding-3-large", "name": "text-embedding-3-large (3072维)", "dim": 3072},
        ],
        "base_url": "https://api.openai.com/v1/embeddings",
        "api_type": "openai"
    }
}


@dataclass
class ConfigStore:
    """配置存储结构"""
    api_configs: list[dict] = field(default_factory=list)
    active_config: str = "default"
    categories: list[str] = field(default_factory=lambda: [
        "SLG", "MMO", "休闲", "卡牌", "二次元", "模拟经营"
    ])


class APIManager:
    """API 配置管理器"""
    
    def __init__(self, config_path: str = "./data/config.json"):
        """初始化 API 管理器"""
        self.config_path = Path(config_path)
        self._current_config: Optional[APIConfig] = None
        self._client: Optional[OpenAI] = None
        self._store: Optional[ConfigStore] = None
        
        # 确保数据目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 启动时自动加载配置
        self._load_store()
    
    def _load_store(self) -> None:
        """加载配置存储"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._store = ConfigStore(
                        api_configs=data.get('api_configs', []),
                        active_config=data.get('active_config', 'default'),
                        categories=data.get('categories', ConfigStore().categories)
                    )
                    # 加载活动配置
                    self._load_active_config()
            except (json.JSONDecodeError, KeyError):
                self._store = ConfigStore()
        else:
            self._store = ConfigStore()
    
    def _save_store(self) -> bool:
        """保存配置存储"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'api_configs': self._store.api_configs,
                    'active_config': self._store.active_config,
                    'categories': self._store.categories
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def _load_active_config(self) -> None:
        """加载当前活动的配置"""
        if not self._store or not self._store.api_configs:
            return
        
        for config_dict in self._store.api_configs:
            if config_dict.get('name') == self._store.active_config:
                self._current_config = APIConfig(
                    api_key=config_dict.get('api_key', ''),
                    base_url=config_dict.get('base_url', ''),
                    model_id=config_dict.get('model_id', ''),
                    name=config_dict.get('name', 'default'),
                    embedding_model=config_dict.get('embedding_model', ''),
                    embedding_base_url=config_dict.get('embedding_base_url', '')
                )
                self._client = None  # 重置客户端，下次使用时重新创建
                break

    def save_config(self, config: APIConfig) -> tuple[bool, str]:
        """
        保存 API 配置到本地
        
        Args:
            config: API 配置对象
            
        Returns:
            (成功标志, 错误信息)
        """
        # 验证配置
        is_valid, error_msg = config.is_valid()
        if not is_valid:
            return False, error_msg
        
        # 更新或添加配置
        config_dict = asdict(config)
        found = False
        for i, existing in enumerate(self._store.api_configs):
            if existing.get('name') == config.name:
                self._store.api_configs[i] = config_dict
                found = True
                break
        
        if not found:
            self._store.api_configs.append(config_dict)
        
        # 保存到文件
        if not self._save_store():
            return False, "保存配置文件失败"
        
        # 如果是当前活动配置，更新内存中的配置
        if config.name == self._store.active_config:
            self._current_config = config
            self._client = None  # 重置客户端
        
        return True, ""
    
    def load_config(self) -> Optional[APIConfig]:
        """
        加载已保存的 API 配置
        
        Returns:
            当前活动的 API 配置，如果没有则返回 None
        """
        return self._current_config
    
    def get_all_configs(self) -> list[APIConfig]:
        """获取所有已保存的配置"""
        configs = []
        for config_dict in self._store.api_configs:
            configs.append(APIConfig(
                api_key=config_dict.get('api_key', ''),
                base_url=config_dict.get('base_url', ''),
                model_id=config_dict.get('model_id', ''),
                name=config_dict.get('name', 'default'),
                embedding_model=config_dict.get('embedding_model', ''),
                embedding_base_url=config_dict.get('embedding_base_url', '')
            ))
        return configs
    
    def switch_config(self, config_name: str) -> tuple[bool, str]:
        """
        切换到指定的配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            (成功标志, 错误信息)
        """
        # 查找配置
        found = False
        for config_dict in self._store.api_configs:
            if config_dict.get('name') == config_name:
                self._current_config = APIConfig(
                    api_key=config_dict.get('api_key', ''),
                    base_url=config_dict.get('base_url', ''),
                    model_id=config_dict.get('model_id', ''),
                    name=config_dict.get('name', 'default'),
                    embedding_model=config_dict.get('embedding_model', ''),
                    embedding_base_url=config_dict.get('embedding_base_url', '')
                )
                found = True
                break
        
        if not found:
            return False, f"配置 '{config_name}' 不存在"
        
        # 更新活动配置
        self._store.active_config = config_name
        self._client = None  # 重置客户端
        
        # 保存更改
        if not self._save_store():
            return False, "保存配置文件失败"
        
        return True, ""
    
    def delete_config(self, config_name: str) -> tuple[bool, str]:
        """
        删除指定的配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            (成功标志, 错误信息)
        """
        # 不能删除当前活动配置
        if config_name == self._store.active_config:
            return False, "不能删除当前活动的配置"
        
        # 查找并删除
        for i, config_dict in enumerate(self._store.api_configs):
            if config_dict.get('name') == config_name:
                self._store.api_configs.pop(i)
                if not self._save_store():
                    return False, "保存配置文件失败"
                return True, ""
        
        return False, f"配置 '{config_name}' 不存在"

    def get_llm_client(self) -> Optional[OpenAI]:
        """
        获取 OpenAI 兼容的 LLM 客户端
        
        Returns:
            OpenAI 客户端实例，如果配置无效则返回 None
        """
        if not self._current_config:
            return None
        
        # 验证配置
        is_valid, _ = self._current_config.is_valid()
        if not is_valid:
            return None
        
        # 如果客户端已存在且配置未变，直接返回
        if self._client is not None:
            return self._client
        
        # 创建新客户端
        try:
            self._client = OpenAI(
                api_key=self._current_config.api_key,
                base_url=self._current_config.base_url
            )
            return self._client
        except Exception:
            return None
    
    def test_connection(self) -> tuple[bool, str]:
        """
        测试 API 连接是否有效
        
        Returns:
            (成功标志, 消息)
        """
        if not self._current_config:
            return False, "未配置 API"
        
        # 验证配置格式
        is_valid, error_msg = self._current_config.is_valid()
        if not is_valid:
            return False, error_msg
        
        client = self.get_llm_client()
        if not client:
            return False, "无法创建 API 客户端"
        
        try:
            # 发送一个简单的测试请求
            response = client.chat.completions.create(
                model=self._current_config.model_id,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True, "连接成功"
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
                return False, "API Key 无效，请检查配置"
            elif "timeout" in error_str:
                return False, "连接超时，请检查网络或 Base URL"
            elif "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
                return False, "模型 ID 不存在，请检查配置"
            elif "rate" in error_str and "limit" in error_str:
                return False, "请求过于频繁，请稍后重试"
            else:
                return False, f"连接失败: {str(e)}"
    
    def stream_chat(
        self, 
        messages: list[dict], 
        **kwargs
    ) -> Generator[str, None, None]:
        """
        流式调用 LLM
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数传递给 API
            
        Yields:
            生成的文本片段
        """
        if not self._current_config:
            yield "[错误] 未配置 API"
            return
        
        client = self.get_llm_client()
        if not client:
            yield "[错误] 无法创建 API 客户端"
            return
        
        try:
            response = client.chat.completions.create(
                model=self._current_config.model_id,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str:
                yield "[错误] API Key 无效，请检查配置"
            elif "timeout" in error_str:
                yield "[错误] 连接超时，请检查网络或 Base URL"
            elif "model" in error_str and "not found" in error_str:
                yield "[错误] 模型 ID 不存在，请检查配置"
            elif "rate" in error_str and "limit" in error_str:
                yield "[错误] 请求过于频繁，请稍后重试"
            else:
                yield f"[错误] {str(e)}"
    
    def chat(self, messages: list[dict], **kwargs) -> tuple[bool, str]:
        """
        非流式调用 LLM
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            (成功标志, 响应内容或错误信息)
        """
        if not self._current_config:
            return False, "未配置 API"
        
        client = self.get_llm_client()
        if not client:
            return False, "无法创建 API 客户端"
        
        try:
            response = client.chat.completions.create(
                model=self._current_config.model_id,
                messages=messages,
                stream=False,
                **kwargs
            )
            
            if response.choices and response.choices[0].message.content:
                return True, response.choices[0].message.content
            return False, "API 返回空响应"
            
        except Exception as e:
            error_str = str(e).lower()
            if "api key" in error_str or "authentication" in error_str:
                return False, "API Key 无效，请检查配置"
            elif "timeout" in error_str:
                return False, "连接超时，请检查网络或 Base URL"
            elif "model" in error_str and "not found" in error_str:
                return False, "模型 ID 不存在，请检查配置"
            elif "rate" in error_str and "limit" in error_str:
                return False, "请求过于频繁，请稍后重试"
            else:
                return False, f"调用失败: {str(e)}"
    
    def get_categories(self) -> list[str]:
        """获取游戏品类列表"""
        return self._store.categories if self._store else []
    
    def get_active_config_name(self) -> str:
        """获取当前活动配置的名称"""
        return self._store.active_config if self._store else "default"
