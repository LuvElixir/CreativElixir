"""
RAG 知识库系统模块

基于本地文件存储的检索系统，支持按游戏品类分类存储和检索脚本。
当 ChromaDB 可用时使用向量检索，否则使用简单的关键词匹配。
"""

import json
import os
import shutil
import uuid
import zipfile
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

# 尝试导入向量数据库，优先使用 FAISS
try:
    import faiss
    import pickle
    FAISS_AVAILABLE = True
    CHROMADB_AVAILABLE = False
except ImportError:
    FAISS_AVAILABLE = False
    try:
        import chromadb
        from chromadb.config import Settings
        CHROMADB_AVAILABLE = True
    except ImportError:
        CHROMADB_AVAILABLE = False


@dataclass
class ScriptMetadata:
    """脚本元数据"""
    game_name: str = ""
    performance: str = ""  # 爆款、普通等
    source: str = "user_archive"  # user_archive, import
    archived_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Script:
    """脚本数据类"""
    id: str
    content: str
    category: str
    metadata: ScriptMetadata
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "metadata": asdict(self.metadata)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Script":
        """从字典创建"""
        metadata = ScriptMetadata(**data.get("metadata", {}))
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            category=data.get("category", ""),
            metadata=metadata
        )


class RAGSystem:
    """RAG 知识库系统"""
    
    def __init__(
        self,
        vector_db_path: str = "./data/vector_db",
        scripts_path: str = "./data/scripts",
        api_manager=None
    ):
        """
        初始化 RAG 系统
        
        Args:
            vector_db_path: 向量数据库存储路径
            scripts_path: 原始脚本数据存储路径
            api_manager: API 管理器实例，用于调用 embedding 模型
        """
        self.vector_db_path = Path(vector_db_path)
        self.scripts_path = Path(scripts_path)
        self._api_manager = api_manager
        
        # 确保目录存在
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.scripts_path.mkdir(parents=True, exist_ok=True)
        
        # 默认品类列表
        self._default_categories = [
            "SLG", "MMO", "休闲", "卡牌", "二次元", "模拟经营"
        ]
        
        # 初始化存储后端
        self._client = None
        self._use_vector_db = FAISS_AVAILABLE or CHROMADB_AVAILABLE
        self._use_faiss = FAISS_AVAILABLE
        
        # FAISS 相关 - 豆包 embedding 模型维度是 2048
        self._embedding_dim = 2048  # doubao-embedding-vision-250615 的维度
        self._faiss_indices = {}  # 每个品类一个索引
        self._faiss_embeddings = {}  # 存储文本嵌入
        self._faiss_metadata = {}  # 存储元数据
        
        if FAISS_AVAILABLE:
            # 使用 FAISS
            self._init_faiss()
        elif CHROMADB_AVAILABLE:
            # 使用 ChromaDB
            try:
                self._client = chromadb.PersistentClient(
                    path=str(self.vector_db_path),
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception:
                self._use_vector_db = False
    
    def _init_faiss(self):
        """初始化 FAISS 索引"""
        if not FAISS_AVAILABLE:
            return
        
        # 为每个品类创建索引文件路径
        for category in self._default_categories:
            index_file = self.vector_db_path / f"{category}.faiss"
            metadata_file = self.vector_db_path / f"{category}_metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                # 加载现有索引
                try:
                    self._faiss_indices[category] = faiss.read_index(str(index_file))
                    with open(metadata_file, 'rb') as f:
                        self._faiss_metadata[category] = pickle.load(f)
                except Exception:
                    # 创建新索引
                    self._faiss_indices[category] = faiss.IndexFlatL2(self._embedding_dim)
                    self._faiss_metadata[category] = []
            else:
                # 创建新索引
                self._faiss_indices[category] = faiss.IndexFlatL2(self._embedding_dim)
                self._faiss_metadata[category] = []
    
    def _ensure_faiss_index(self, category: str, embedding_dim: int):
        """确保 FAISS 索引存在且维度正确"""
        if not FAISS_AVAILABLE:
            return
        
        # 如果索引不存在或维度不匹配，创建新索引
        if (category not in self._faiss_indices or 
            self._faiss_indices[category].d != embedding_dim):
            
            # 更新全局维度设置
            if self._embedding_dim != embedding_dim:
                self._embedding_dim = embedding_dim
                print(f"更新 embedding 维度为: {embedding_dim}")
            
            # 创建新索引
            self._faiss_indices[category] = faiss.IndexFlatL2(embedding_dim)
            if category not in self._faiss_metadata:
                self._faiss_metadata[category] = []
            
            print(f"为品类 {category} 创建 {embedding_dim} 维 FAISS 索引")
    
    def _save_faiss_index(self, category: str):
        """保存 FAISS 索引到文件"""
        if not self._use_faiss or category not in self._faiss_indices:
            return
        
        try:
            index_file = self.vector_db_path / f"{category}.faiss"
            metadata_file = self.vector_db_path / f"{category}_metadata.pkl"
            
            faiss.write_index(self._faiss_indices[category], str(index_file))
            with open(metadata_file, 'wb') as f:
                pickle.dump(self._faiss_metadata[category], f)
        except Exception:
            pass
    
    def _get_text_embedding(self, text: str):
        """获取文本嵌入 - 使用配置的 Embedding 模型"""
        if not hasattr(self, '_api_manager') or not self._api_manager:
            raise ValueError("未配置 API 管理器，无法使用知识库功能")
        
        config = self._api_manager.load_config()
        if not config:
            raise ValueError("未配置 API，请先在侧边栏配置 API 设置")
        
        if not config.has_embedding_config():
            raise ValueError("未配置 Embedding 模型，请在 API 设置中选择 Embedding 模型")
        
        import numpy as np
        
        # 根据 embedding_base_url 判断 API 类型
        embedding_url = config.embedding_base_url or config.base_url
        
        # 豆包 API（火山引擎）
        if 'volces.com' in embedding_url or 'ark' in embedding_url:
            embedding = self._get_doubao_embedding(config, text)
        # 硅基流动 API
        elif 'siliconflow' in embedding_url:
            embedding = self._get_siliconflow_embedding(config, text)
        # OpenAI 兼容 API
        else:
            embedding = self._get_openai_embedding(config, text)
        
        if embedding is None:
            raise ValueError("Embedding 生成失败，请检查 API 配置和网络连接")
        
        return embedding
    
    def _get_doubao_embedding(self, config, text: str):
        """获取豆包（火山引擎）的 embedding"""
        import requests
        import numpy as np
        
        try:
            # 豆包 embedding API 端点
            url = config.embedding_base_url or "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}"
            }
            
            payload = {
                "model": config.embedding_model,
                "input": [
                    {
                        "type": "text",
                        "text": text[:8000]  # 限制文本长度
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result:
                    data = result["data"]
                    # 豆包的响应格式是 data.embedding 而不是 data[0].embedding
                    if isinstance(data, dict):
                        embedding = data.get("embedding", [])
                    elif isinstance(data, list) and len(data) > 0:
                        embedding = data[0].get("embedding", [])
                    else:
                        embedding = []
                    
                    if embedding:
                        embedding_array = np.array(embedding, dtype=np.float32)
                        return self._normalize_embedding(embedding_array)
            
            print(f"豆包 embedding 返回状态码: {response.status_code}, 响应: {response.text[:200]}")
            return None
            
        except Exception as e:
            print(f"豆包 embedding 调用异常: {e}")
            return None
    
    def _get_siliconflow_embedding(self, config, text: str):
        """获取硅基流动的 embedding"""
        import requests
        import numpy as np
        
        try:
            url = config.embedding_base_url or "https://api.siliconflow.cn/v1/embeddings"
            
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config.embedding_model,
                "input": text[:8000],  # 限制文本长度
                "encoding_format": "float"
            }
            
            # 对于 Qwen 系列模型，可以指定维度
            if "Qwen" in config.embedding_model:
                payload["dimensions"] = 1024
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0].get("embedding", [])
                    if embedding:
                        embedding_array = np.array(embedding, dtype=np.float32)
                        return self._normalize_embedding(embedding_array)
            
            print(f"硅基流动 embedding 返回状态码: {response.status_code}, 响应: {response.text[:200]}")
            return None
            
        except Exception as e:
            print(f"硅基流动 embedding 调用异常: {e}")
            return None
    
    def _get_openai_embedding(self, config, text: str):
        """获取 OpenAI 兼容的 embedding"""
        import numpy as np
        
        try:
            from openai import OpenAI
            
            base_url = config.embedding_base_url or config.base_url
            
            client = OpenAI(
                api_key=config.api_key,
                base_url=base_url
            )
            
            response = client.embeddings.create(
                model=config.embedding_model,
                input=text[:8000]
            )
            
            if response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                embedding_array = np.array(embedding, dtype=np.float32)
                return self._normalize_embedding(embedding_array)
            
            return None
            
        except Exception as e:
            print(f"OpenAI embedding 调用异常: {e}")
            return None
    
    def _normalize_embedding(self, embedding_array):
        """归一化 embedding 向量"""
        import numpy as np
        
        # 动态调整维度
        actual_dim = len(embedding_array)
        if actual_dim != self._embedding_dim:
            self._embedding_dim = actual_dim
        
        # 归一化
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
        
        return embedding_array

    
    def _add_to_faiss(self, script: Script):
        """添加脚本到 FAISS 索引"""
        if not self._use_faiss:
            return
        
        try:
            # 获取文本嵌入
            embedding = self._get_text_embedding(script.content)
            
            # 如果 embedding 为 None，跳过向量索引
            if embedding is None:
                print("向量数据库添加失败（embedding 不可用）")
                return
            
            # 确保索引存在且维度正确
            self._ensure_faiss_index(script.category, len(embedding))
            
            # 添加到索引
            import numpy as np
            embedding_array = np.array([embedding], dtype=np.float32)
            self._faiss_indices[script.category].add(embedding_array)
            
            # 添加元数据
            self._faiss_metadata[script.category].append({
                "id": script.id,
                "content": script.content,
                "category": script.category,
                "metadata": asdict(script.metadata)
            })
            
            # 保存索引
            self._save_faiss_index(script.category)
            
        except Exception as e:
            print(f"FAISS 添加失败: {e}")
    
    def _search_faiss(self, query: str, category: str, top_k: int = 5) -> list[Script]:
        """使用 FAISS 搜索"""
        if not self._use_faiss or category not in self._faiss_indices:
            return []
        
        try:
            # 获取查询嵌入
            query_embedding = self._get_text_embedding(query)
            
            # 如果 embedding 为 None，返回空列表（回退到简单搜索）
            if query_embedding is None:
                return []
            
            # 搜索
            import numpy as np
            query_array = np.array([query_embedding], dtype=np.float32)
            
            index = self._faiss_indices[category]
            if index.ntotal == 0:  # 索引为空
                return []
            
            # 执行搜索
            distances, indices = index.search(query_array, min(top_k, index.ntotal))
            
            # 构建结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self._faiss_metadata[category]):
                    metadata_item = self._faiss_metadata[category][idx]
                    script = Script(
                        id=metadata_item["id"],
                        content=metadata_item["content"],
                        category=metadata_item["category"],
                        metadata=ScriptMetadata(**metadata_item["metadata"])
                    )
                    results.append(script)
            
            return results
            
        except Exception as e:
            print(f"FAISS 搜索失败: {e}")
            return []

    def _get_collection(self, category: str):
        """
        获取或创建指定品类的集合
        
        Args:
            category: 游戏品类
            
        Returns:
            ChromaDB 集合或 None
        """
        if self._use_faiss:
            # FAISS 模式下，确保索引存在（维度会在添加时动态调整）
            if category not in self._faiss_indices:
                # 先创建一个默认维度的索引，实际维度会在第一次添加时确定
                self._faiss_indices[category] = faiss.IndexFlatL2(self._embedding_dim)
                self._faiss_metadata[category] = []
            return category
        elif CHROMADB_AVAILABLE and self._client:
            # ChromaDB 模式
            collection_name = f"scripts_{category.replace(' ', '_')}"
            return self._client.get_or_create_collection(
                name=collection_name,
                metadata={"category": category}
            )
        return None
    
    def is_vector_db_available(self) -> bool:
        """检查向量数据库是否可用"""
        return self._use_vector_db
    
    def update_api_manager(self, api_manager):
        """更新 API 管理器实例"""
        self._api_manager = api_manager
    
    def is_chromadb_available(self) -> bool:
        """检查 ChromaDB 是否可用（保持向后兼容）"""
        return CHROMADB_AVAILABLE and not self._use_faiss
    
    def _save_script_file(self, script: Script) -> bool:
        """
        保存脚本到文件系统
        
        Args:
            script: 脚本对象
            
        Returns:
            是否保存成功
        """
        try:
            category_path = self.scripts_path / script.category
            category_path.mkdir(parents=True, exist_ok=True)
            
            script_file = category_path / f"{script.id}.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def _load_script_file(self, category: str, script_id: str) -> Optional[Script]:
        """
        从文件系统加载脚本
        
        Args:
            category: 游戏品类
            script_id: 脚本 ID
            
        Returns:
            脚本对象，如果不存在则返回 None
        """
        try:
            script_file = self.scripts_path / category / f"{script_id}.json"
            if not script_file.exists():
                return None
            
            with open(script_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Script.from_dict(data)
        except Exception:
            return None
    
    def _delete_script_file(self, category: str, script_id: str) -> bool:
        """
        从文件系统删除脚本
        
        Args:
            category: 游戏品类
            script_id: 脚本 ID
            
        Returns:
            是否删除成功
        """
        try:
            script_file = self.scripts_path / category / f"{script_id}.json"
            if script_file.exists():
                script_file.unlink()
            return True
        except Exception:
            return False

    def _simple_search(self, query: str, category: str, top_k: int = 5) -> list[Script]:
        """
        简单的关键词搜索（非 ChromaDB 模式）
        
        Args:
            query: 查询文本
            category: 游戏品类
            top_k: 返回结果数量
            
        Returns:
            相关脚本列表
        """
        scripts = self.get_scripts_by_category(category)
        if not scripts:
            return []
        
        # 简单的关键词匹配评分
        query_terms = set(query.lower().split())
        scored_scripts = []
        
        for script in scripts:
            content_lower = script.content.lower()
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                scored_scripts.append((score, script))
        
        # 按分数排序并返回 top_k
        scored_scripts.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored_scripts[:top_k]]

    def add_script(
        self,
        content: str,
        category: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        添加脚本到知识库
        
        Args:
            content: 脚本内容
            category: 游戏品类（SLG、MMO、休闲等）
            metadata: 可选的元数据字典
            
        Returns:
            文档 ID
        """
        # 生成唯一 ID
        doc_id = str(uuid.uuid4())
        
        # 创建元数据对象
        script_metadata = ScriptMetadata(**(metadata or {}))
        
        # 创建脚本对象
        script = Script(
            id=doc_id,
            content=content,
            category=category,
            metadata=script_metadata
        )
        
        # 保存到文件系统
        self._save_script_file(script)
        
        # 添加到向量数据库
        vector_success = False
        if self._use_vector_db:
            try:
                if self._use_faiss:
                    # 使用 FAISS
                    self._add_to_faiss(script)
                    vector_success = True
                elif CHROMADB_AVAILABLE and self._client:
                    # 使用 ChromaDB
                    collection = self._get_collection(category)
                    if collection:
                        collection.add(
                            ids=[doc_id],
                            documents=[content],
                            metadatas=[{
                                "category": category,
                                "game_name": script_metadata.game_name,
                                "performance": script_metadata.performance,
                                "source": script_metadata.source,
                                "archived_at": script_metadata.archived_at
                            }]
                        )
                        vector_success = True
            except ValueError as e:
                # embedding 相关错误，记录但不影响文件存储
                print(f"向量数据库添加失败（embedding 不可用）: {e}")
            except Exception as e:
                # 其他错误，记录但不影响文件存储
                print(f"向量数据库添加失败: {e}")
        
        if not vector_success and self._use_vector_db:
            print(f"脚本已保存到文件系统，但向量检索功能不可用")
        
        return doc_id

    def search(
        self,
        query: str,
        category: str,
        top_k: int = 5
    ) -> list[Script]:
        """
        检索同品类相关脚本
        
        Args:
            query: 查询文本
            category: 游戏品类
            top_k: 返回结果数量
            
        Returns:
            相关脚本列表
        """
        # 首先尝试使用向量检索
        if self._use_vector_db:
            try:
                if self._use_faiss:
                    # 使用 FAISS 搜索
                    results = self._search_faiss(query, category, top_k)
                    # 如果 FAISS 返回结果，直接返回；否则回退到简单搜索
                    if results:
                        return results
                elif CHROMADB_AVAILABLE and self._client:
                    # 使用 ChromaDB 搜索
                    collection = self._get_collection(category)
                    if collection and collection.count() > 0:
                        results = collection.query(
                            query_texts=[query],
                            n_results=min(top_k, collection.count())
                        )
                        
                        scripts = []
                        if results and results['ids'] and results['ids'][0]:
                            for i, doc_id in enumerate(results['ids'][0]):
                                # 尝试从文件加载完整脚本
                                script = self._load_script_file(category, doc_id)
                                if script:
                                    scripts.append(script)
                                elif results['documents'] and results['documents'][0]:
                                    # 如果文件不存在，从查询结果构建
                                    metadata_dict = results['metadatas'][0][i] if results['metadatas'] else {}
                                    scripts.append(Script(
                                        id=doc_id,
                                        content=results['documents'][0][i],
                                        category=category,
                                        metadata=ScriptMetadata(
                                            game_name=metadata_dict.get('game_name', ''),
                                            performance=metadata_dict.get('performance', ''),
                                            source=metadata_dict.get('source', ''),
                                            archived_at=metadata_dict.get('archived_at', '')
                                        )
                                    ))
                        return scripts
            except ValueError as e:
                # embedding 相关错误，回退到简单搜索
                print(f"向量检索失败，回退到关键词搜索: {e}")
            except Exception as e:
                # 其他错误，回退到简单搜索
                print(f"向量检索失败，回退到关键词搜索: {e}")
        
        # 回退到简单搜索
        return self._simple_search(query, category, top_k)
    
    def get_script(self, category: str, doc_id: str) -> Optional[Script]:
        """
        获取指定脚本
        
        Args:
            category: 游戏品类
            doc_id: 文档 ID
            
        Returns:
            脚本对象，如果不存在则返回 None
        """
        return self._load_script_file(category, doc_id)
    
    def get_scripts_by_category(self, category: str) -> list[Script]:
        """
        获取指定品类的所有脚本
        
        Args:
            category: 游戏品类
            
        Returns:
            脚本列表
        """
        scripts = []
        category_path = self.scripts_path / category
        
        if not category_path.exists():
            return scripts
        
        for script_file in category_path.glob("*.json"):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                scripts.append(Script.from_dict(data))
            except Exception:
                continue
        
        return scripts
    
    def delete_script(self, doc_id: str) -> bool:
        """
        删除指定脚本
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否删除成功
        """
        # 查找脚本所在的品类
        for category_dir in self.scripts_path.iterdir():
            if category_dir.is_dir():
                script_file = category_dir / f"{doc_id}.json"
                if script_file.exists():
                    category = category_dir.name
                    
                    # 从向量数据库删除
                    if self._use_faiss and category in self._faiss_indices:
                        try:
                            # FAISS 不支持直接删除，需要重建索引
                            # 这里简化处理，只从元数据中移除
                            metadata_list = self._faiss_metadata.get(category, [])
                            self._faiss_metadata[category] = [
                                item for item in metadata_list if item["id"] != doc_id
                            ]
                            self._save_faiss_index(category)
                        except Exception:
                            pass
                    elif CHROMADB_AVAILABLE and self._client:
                        try:
                            collection = self._get_collection(category)
                            if collection:
                                collection.delete(ids=[doc_id])
                        except Exception:
                            pass
                    
                    # 从文件系统删除
                    return self._delete_script_file(category, doc_id)
        
        return False
    
    def get_categories(self) -> list[str]:
        """
        获取所有游戏品类
        
        Returns:
            品类列表（包含默认品类和已有数据的品类）
        """
        categories = set(self._default_categories)
        
        # 添加已有数据的品类
        if self.scripts_path.exists():
            for category_dir in self.scripts_path.iterdir():
                if category_dir.is_dir() and any(category_dir.glob("*.json")):
                    categories.add(category_dir.name)
        
        return sorted(list(categories))
    
    def get_script_count(self, category: Optional[str] = None) -> int:
        """
        获取脚本数量
        
        Args:
            category: 可选的品类筛选
            
        Returns:
            脚本数量
        """
        count = 0
        
        if category:
            category_path = self.scripts_path / category
            if category_path.exists():
                count = len(list(category_path.glob("*.json")))
        else:
            for category_dir in self.scripts_path.iterdir():
                if category_dir.is_dir():
                    count += len(list(category_dir.glob("*.json")))
        
        return count

    def export_knowledge_base(self, output_path: str) -> tuple[bool, str]:
        """
        导出知识库为 zip 文件
        
        Args:
            output_path: 输出文件路径（不含扩展名）
            
        Returns:
            (成功标志, zip 文件路径或错误信息)
        """
        try:
            # 确保输出目录存在
            output_file = Path(output_path)
            if not output_file.suffix:
                output_file = output_file.with_suffix('.zip')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建临时导出目录
            temp_export_dir = self.scripts_path.parent / "_export_temp"
            if temp_export_dir.exists():
                shutil.rmtree(temp_export_dir)
            temp_export_dir.mkdir(parents=True)
            
            # 复制脚本文件
            scripts_export = temp_export_dir / "scripts"
            if self.scripts_path.exists():
                shutil.copytree(self.scripts_path, scripts_export)
            else:
                scripts_export.mkdir(parents=True)
            
            # 复制向量数据库（如果存在）
            vector_export = temp_export_dir / "vector_db"
            if self.vector_db_path.exists() and any(self.vector_db_path.iterdir()):
                shutil.copytree(self.vector_db_path, vector_export)
            else:
                vector_export.mkdir(parents=True)
            
            # 创建元数据文件
            metadata = {
                "export_time": datetime.now().isoformat(),
                "version": "1.0",
                "categories": self.get_categories(),
                "total_scripts": self.get_script_count(),
                "chromadb_available": CHROMADB_AVAILABLE and not self._use_faiss
            }
            with open(temp_export_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 打包为 zip
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_export_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(temp_export_dir)
                        zf.write(file_path, arcname)
            
            # 清理临时目录
            shutil.rmtree(temp_export_dir)
            
            return True, str(output_file)
            
        except Exception as e:
            # 清理临时目录
            temp_export_dir = self.scripts_path.parent / "_export_temp"
            if temp_export_dir.exists():
                shutil.rmtree(temp_export_dir)
            return False, f"导出失败: {str(e)}"
    
    def import_knowledge_base(self, zip_path: str) -> tuple[bool, str]:
        """
        导入知识库 zip 文件
        
        Args:
            zip_path: zip 文件路径
            
        Returns:
            (成功标志, 成功消息或错误信息)
        """
        try:
            zip_file = Path(zip_path)
            if not zip_file.exists():
                return False, "文件不存在"
            
            if not zipfile.is_zipfile(zip_file):
                return False, "文件格式不正确，请上传有效的知识库导出文件"
            
            # 创建临时解压目录
            temp_import_dir = self.scripts_path.parent / "_import_temp"
            if temp_import_dir.exists():
                shutil.rmtree(temp_import_dir)
            temp_import_dir.mkdir(parents=True)
            
            # 解压文件
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(temp_import_dir)
            
            # 验证导入文件结构
            scripts_import = temp_import_dir / "scripts"
            vector_import = temp_import_dir / "vector_db"
            
            if not scripts_import.exists() and not vector_import.exists():
                shutil.rmtree(temp_import_dir)
                return False, "文件格式不正确，缺少必要的数据目录"
            
            # 关闭当前连接
            if CHROMADB_AVAILABLE and self._client:
                self._client = None
            
            # 备份现有数据
            backup_scripts = None
            backup_vector = None
            
            if self.scripts_path.exists():
                backup_scripts = self.scripts_path.parent / "_scripts_backup"
                if backup_scripts.exists():
                    shutil.rmtree(backup_scripts)
                shutil.move(str(self.scripts_path), str(backup_scripts))
            
            if self.vector_db_path.exists():
                backup_vector = self.vector_db_path.parent / "_vector_backup"
                if backup_vector.exists():
                    shutil.rmtree(backup_vector)
                shutil.move(str(self.vector_db_path), str(backup_vector))
            
            try:
                # 导入脚本文件
                if scripts_import.exists():
                    shutil.copytree(scripts_import, self.scripts_path)
                else:
                    self.scripts_path.mkdir(parents=True)
                
                # 导入向量数据库
                if vector_import.exists():
                    shutil.copytree(vector_import, self.vector_db_path)
                else:
                    self.vector_db_path.mkdir(parents=True)
                
                # 重新初始化客户端
                if CHROMADB_AVAILABLE and not self._use_faiss:
                    try:
                        self._client = chromadb.PersistentClient(
                            path=str(self.vector_db_path),
                            settings=Settings(anonymized_telemetry=False)
                        )
                    except Exception:
                        pass
                elif FAISS_AVAILABLE:
                    # 重新初始化 FAISS 索引
                    self._init_faiss()
                
                # 清理备份和临时目录
                if backup_scripts and backup_scripts.exists():
                    shutil.rmtree(backup_scripts)
                if backup_vector and backup_vector.exists():
                    shutil.rmtree(backup_vector)
                shutil.rmtree(temp_import_dir)
                
                # 获取导入的脚本数量
                imported_count = self.get_script_count()
                
                return True, f"导入成功，共导入 {imported_count} 个脚本"
                
            except Exception as e:
                # 恢复备份
                if self.scripts_path.exists():
                    shutil.rmtree(self.scripts_path)
                if self.vector_db_path.exists():
                    shutil.rmtree(self.vector_db_path)
                
                if backup_scripts and backup_scripts.exists():
                    shutil.move(str(backup_scripts), str(self.scripts_path))
                if backup_vector and backup_vector.exists():
                    shutil.move(str(backup_vector), str(self.vector_db_path))
                
                # 重新初始化客户端
                if CHROMADB_AVAILABLE and not self._use_faiss:
                    try:
                        self._client = chromadb.PersistentClient(
                            path=str(self.vector_db_path),
                            settings=Settings(anonymized_telemetry=False)
                        )
                    except Exception:
                        pass
                elif FAISS_AVAILABLE:
                    # 重新初始化 FAISS 索引
                    self._init_faiss()
                
                raise e
                
        except Exception as e:
            # 清理临时目录
            temp_import_dir = self.scripts_path.parent / "_import_temp"
            if temp_import_dir.exists():
                shutil.rmtree(temp_import_dir)
            return False, f"导入失败: {str(e)}"
    
    def clear_knowledge_base(self) -> tuple[bool, str]:
        """
        清空知识库
        
        Returns:
            (成功标志, 消息)
        """
        try:
            # 关闭连接
            if CHROMADB_AVAILABLE and self._client:
                self._client = None
            
            # 删除脚本文件
            if self.scripts_path.exists():
                shutil.rmtree(self.scripts_path)
            self.scripts_path.mkdir(parents=True)
            
            # 删除向量数据库
            if self.vector_db_path.exists():
                shutil.rmtree(self.vector_db_path)
            self.vector_db_path.mkdir(parents=True)
            
            # 重新初始化客户端
            if CHROMADB_AVAILABLE and not self._use_faiss:
                try:
                    self._client = chromadb.PersistentClient(
                        path=str(self.vector_db_path),
                        settings=Settings(anonymized_telemetry=False)
                    )
                except Exception:
                    pass
            elif FAISS_AVAILABLE:
                # 重新初始化 FAISS 索引
                self._init_faiss()
            
            return True, "知识库已清空"
            
        except Exception as e:
            return False, f"清空失败: {str(e)}"
    
    def is_chromadb_available(self) -> bool:
        """
        检查 ChromaDB 是否可用
        
        Returns:
            是否可用
        """
        return self._use_chromadb
