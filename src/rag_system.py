"""
RAG 知识库系统模块

基于本地文件存储的检索系统，支持按游戏品类分类存储和检索脚本。
当 ChromaDB 可用时使用向量检索，否则使用简单的关键词匹配。
"""

import json
import os
import re
import shutil
import uuid
import zipfile
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable, Union

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
class EnhancedScriptMetadata:
    """增强型脚本元数据，支持丰富的标签体系以实现精准检索"""
    game_name: str = "未知"
    category: str = "其他"
    gameplay_tags: list = field(default_factory=list)
    hook_type: str = ""
    visual_style: str = ""
    summary: str = ""
    source: str = "user_capture"
    archived_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @classmethod
    def from_legacy(cls, legacy: ScriptMetadata) -> "EnhancedScriptMetadata":
        """从旧版 ScriptMetadata 转换，保持向后兼容"""
        return cls(
            game_name=legacy.game_name if legacy.game_name else "未知",
            category="其他",
            gameplay_tags=[],
            hook_type="",
            visual_style="",
            summary="",
            source=legacy.source,
            archived_at=legacy.archived_at
        )
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "game_name": self.game_name,
            "category": self.category,
            "gameplay_tags": self.gameplay_tags,
            "hook_type": self.hook_type,
            "visual_style": self.visual_style,
            "summary": self.summary,
            "source": self.source,
            "archived_at": self.archived_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EnhancedScriptMetadata":
        """从字典反序列化，缺失字段使用默认值"""
        return cls(
            game_name=data.get("game_name", "未知"),
            category=data.get("category", "其他"),
            gameplay_tags=data.get("gameplay_tags", []),
            hook_type=data.get("hook_type", ""),
            visual_style=data.get("visual_style", ""),
            summary=data.get("summary", ""),
            source=data.get("source", "user_capture"),
            archived_at=data.get("archived_at", datetime.now().isoformat())
        )


def extract_json_from_response(response: str) -> Optional[dict]:
    """
    尝试从 LLM 响应中提取 JSON
    
    按以下顺序尝试：
    1. 直接尝试 json.loads
    2. 尝试从 ```json ... ``` 代码块提取
    3. 尝试从 ``` ... ``` 代码块提取
    4. 返回 None 表示失败
    
    Args:
        response: LLM 响应字符串
        
    Returns:
        解析后的字典，如果解析失败则返回 None
    """
    if not response or not response.strip():
        return None
    
    # 1. 直接尝试解析
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # 2. 尝试从 ```json 代码块提取
    json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(json_block_pattern, response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 3. 尝试从普通代码块提取
    code_block_pattern = r'```\s*([\s\S]*?)\s*```'
    match = re.search(code_block_pattern, response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    return None


def parse_auto_tag_response(
    response: str
) -> tuple[bool, Union[EnhancedScriptMetadata, str], Optional[str]]:
    """
    解析 LLM 自动打标响应
    
    Args:
        response: LLM 响应字符串
        
    Returns:
        (success, result, raw_response)
        - success: 是否解析成功
        - result: 成功时为 EnhancedScriptMetadata，失败时为错误信息字符串
        - raw_response: 解析失败时包含原始响应用于调试，成功时为 None
    """
    # 检查空响应
    if not response or not response.strip():
        return False, "AI 返回为空", None
    
    # 尝试提取 JSON
    parsed_data = extract_json_from_response(response)
    
    if parsed_data is None:
        # 解析失败，返回错误和原始响应
        return False, "无法解析 JSON", response
    
    # 解析成功，应用默认值并创建 EnhancedScriptMetadata
    metadata = EnhancedScriptMetadata.from_dict(parsed_data)
    
    return True, metadata, None


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
    
    # ==================== 题材特征库 ====================
    THEME_TRAITS = {
        "魔幻": {
            "核心特征": "用户基数大、付费能力强",
            "文案侧重点": [
                "突出画质质感、激烈战斗场面、装备系统",
                "强调'沉浸式奇幻世界观'",
                "强调'高自由度探索'",
                "强调'珍稀装备掉落'"
            ]
        },
        "传奇": {
            "核心特征": "用户忠诚度高，经典玩法黏性强",
            "文案侧重点": [
                "主打'情怀回归''经典复刻'",
                "突出'一刀999''装备全靠打'",
                "强调'自由PK''沙城争霸'等核心爽点"
            ]
        },
        "三国": {
            "核心特征": "策略属性强，用户群体成熟（25-50岁），生命周期长",
            "文案侧重点": [
                "强调历史还原度、策略深度",
                "突出'真实历史地图''海量武将养成'",
                "强调'权谋博弈''万人同屏国战'"
            ]
        },
        "历史": {
            "核心特征": "策略属性强，用户群体成熟（25-50岁），生命周期长",
            "文案侧重点": [
                "强调历史还原度、策略深度",
                "突出'真实历史地图''海量武将养成'",
                "强调'权谋博弈''万人同屏国战'"
            ]
        },
        "战争": {
            "核心特征": "涵盖现代/近代/未来战争，男性用户主导",
            "文案侧重点": [
                "突出'真实战争场景''兵种策略搭配'",
                "强调'大规模团战''武器装备升级'",
                "按细分领域强化差异（如未来战争突出科幻武器）"
            ]
        },
        "武侠": {
            "核心特征": "关联国潮文化，用户对传统文化认同感强",
            "文案侧重点": [
                "营造东方美学意境",
                "突出'轻功快意江湖''武侠情怀还原'",
                "强调'国风画质'"
            ]
        },
        "仙侠": {
            "核心特征": "关联国潮文化，用户对传统文化认同感强",
            "文案侧重点": [
                "营造东方美学意境",
                "突出'仙盟社交''渡劫修仙'",
                "强调'国风画质'"
            ]
        },
        "二次元": {
            "核心特征": "用户年轻化（18-25岁），女性占比高，对IP和画风敏感",
            "文案侧重点": [
                "主打IP联动效应",
                "突出'精美角色立绘''沉浸式剧情'",
                "强调'个性化角色养成''二次元专属世界观'"
            ]
        },
        "现代": {
            "核心特征": "类型多元，适配轻度/中重度玩法，用户分布均衡",
            "文案侧重点": [
                "轻度玩法突出'贴近现实''简单易上手'",
                "中重度玩法强调'真实感代入''都市冒险/职场成长'",
                "强调'即时互动社交'"
            ]
        },
        "都市": {
            "核心特征": "类型多元，适配轻度/中重度玩法，用户分布均衡",
            "文案侧重点": [
                "轻度玩法突出'贴近现实''简单易上手'",
                "中重度玩法强调'真实感代入''都市冒险/职场成长'",
                "强调'即时互动社交'"
            ]
        }
    }
    
    # ==================== 玩法特征库 ====================
    GAMEPLAY_TRAITS = {
        "休闲消除": {
            "核心特征": "用户渗透率56.9%，广告容忍度高（76.4%），全年龄覆盖",
            "文案侧重点": [
                "强调'3秒上手''5秒爽感''轻松解压'",
                "突出'古风/萌系画风''关卡丰富'",
                "强调'消除即得奖励'"
            ]
        },
        "网赚": {
            "核心特征": "增长率最高，用户门槛低，变现直接",
            "文案侧重点": [
                "主打'看广告领红包''零门槛赚钱'",
                "强调'随时提现''轻松躺赚'",
                "强化奖励真实性"
            ]
        },
        "放置挂机": {
            "核心特征": "低操作门槛，离线可成长，适配碎片化时间",
            "文案侧重点": [
                "突出'离线也升级''自动战斗获资源'",
                "强调'上班/摸鱼轻松玩'",
                "新增策略元素则强调'阵容搭配自由''成长路径可控'"
            ]
        },
        "益智解谜": {
            "核心特征": "用户对可玩性要求提升，需差异化创新",
            "文案侧重点": [
                "强调'烧脑趣味''创意关卡设计'",
                "突出'剧情式解谜''解锁隐藏结局'"
            ]
        },
        "传奇ARPG": {
            "核心特征": "玩法成熟，用户黏性强，战斗爽感突出",
            "文案侧重点": [
                "突出'极致打击感''全屏技能特效'",
                "强调'BOSS挑战掉落''快速升级成长'"
            ]
        },
        "卡牌": {
            "核心特征": "开发成本低，生命周期长，适配多元题材",
            "文案侧重点": [
                "强调'海量卡牌收集''策略阵容搭配'",
                "突出'抽卡概率透明''PVP竞技对抗'",
                "融合创新玩法则突出'卡牌+roguelike''卡牌+自走棋'等差异化体验"
            ]
        },
        "射击": {
            "核心特征": "表现突出，细分标签多元（英雄射击/二次元/飞行射击）",
            "文案侧重点": [
                "突出'流畅操作体验''丰富武器系统'",
                "强调'竞技对抗快感'",
                "差异化标签强化'英雄技能策略''二次元画风''空中激战'"
            ]
        }
    }
    
    # ==================== 融合玩法特征库 ====================
    HYBRID_GAMEPLAY_TRAITS = {
        "SLG+副玩法": {
            "文案侧重": "'低获客成本+高社交粘性'",
            "核心卖点": "突出'休闲上手+策略深度'双重体验"
        },
        "消除+X": {
            "文案侧重": "'消除爽感+成长乐趣'",
            "核心卖点": "突出'资源获取-场景升级'闭环体验"
        },
        "放置+X": {
            "文案侧重": "'轻松挂机+沉浸式体验'",
            "核心卖点": "突出'云游挂机''仙盟传功'等特色玩法"
        },
        "射击+X": {
            "文案侧重": "'突破传统射击体验'",
            "核心卖点": "突出'2D/3D形态切换''战术突袭玩法'"
        },
        "MOBA+X": {
            "文案侧重": "'英雄对战+多元策略'",
            "核心卖点": "突出'跨界玩法融合''新手友好'"
        }
    }
    
    # ==================== 高转化特征（按品类） ====================
    HIGH_PERFORMING_TRAITS = {
        "SLG": """【SLG 高转化特征】
核心特征：增长强劲，吸金能力强，头部集中度高，核心用户注重智力挑战

买量文案必备要素：
1. 前3秒必须展示战力数值跳动或地图扩张
2. 必须包含'以弱胜强'的策略反转
3. 突出'深度策略博弈''资源管理规划'
4. 强调'大规模战争场面''联盟社交协作'
5. 融合副玩法则强调'轻松上手+深度策略并存'
6. 结尾强调'开局送连抽'或限时福利""",
        
        "MMO": """【MMO 高转化特征】
核心特征：市场基数大，仍为买量大户，正向轻量化转型

买量文案必备要素：
1. 必须展示高精度捏脸或装备发光特效
2. 轻量化产品突出'低门槛上手''碎片化体验'
3. 传统产品强调'宏大世界观''高清画质'
4. 突出'丰富社交系统''职业多元养成'
5. 强调'自由交易'或'回收'利益点
6. 拒绝长旁白，多用战斗实录""",
        
        "休闲": """【休闲游戏高转化特征】
核心特征：用户渗透率高，广告容忍度高，全年龄覆盖

买量文案必备要素：
1. 前3秒必须展示核心玩法爽感
2. 强调'3秒上手''5秒爽感''轻松解压'
3. 突出'古风/萌系画风''关卡丰富'
4. 消除类强调'消除即得奖励'
5. 网赚类主打'看广告领红包''零门槛赚钱''随时提现'
6. 放置类突出'离线也升级''自动战斗获资源'""",
        
        "卡牌": """【卡牌游戏高转化特征】
核心特征：开发成本低，生命周期长，适配多元题材

买量文案必备要素：
1. 前3秒展示稀有卡牌或抽卡动画
2. 强调'海量卡牌收集''策略阵容搭配'
3. 突出'抽卡概率透明''PVP竞技对抗'
4. 融合创新玩法则突出'卡牌+roguelike''卡牌+自走棋'
5. 二次元卡牌主打IP联动、精美立绘
6. 结尾强调首抽福利或保底机制""",
        
        "二次元": """【二次元游戏高转化特征】
核心特征：用户年轻化（18-25岁），女性占比高，对IP和画风敏感

买量文案必备要素：
1. 前3秒必须展示精美角色立绘或动态CG
2. 主打IP联动效应（如有）
3. 突出'沉浸式剧情''个性化角色养成'
4. 强调'二次元专属世界观'
5. 展示角色语音、Live2D等特色
6. 避免过度商业化表达，保持调性""",
        
        "模拟经营": """【模拟经营高转化特征】
核心特征：用户粘性强，适合长线运营，女性用户占比高

买量文案必备要素：
1. 前3秒展示经营成果或装扮效果
2. 突出'从零开始打造''亲手建设'的成就感
3. 强调'自由装扮''个性化定制'
4. 展示社交互动、好友互访功能
5. 融合消除玩法则突出'资源获取-场景升级'闭环
6. 结尾强调开局福利或限时活动""",
        
        "射击": """【射击游戏高转化特征】
核心特征：表现突出，细分标签多元（英雄射击/二次元/飞行射击）

买量文案必备要素：
1. 前3秒必须展示流畅操作或精彩击杀
2. 突出'流畅操作体验''丰富武器系统'
3. 强调'竞技对抗快感'
4. 英雄射击强化'英雄技能策略'
5. 二次元射击突出'二次元画风'
6. 飞行射击强调'空中激战'体验""",
        
        "传奇": """【传奇游戏高转化特征】
核心特征：用户忠诚度高，经典玩法黏性强，情怀驱动

买量文案必备要素：
1. 前3秒必须展示'一刀999'或爆装备场面
2. 主打'情怀回归''经典复刻'
3. 突出'装备全靠打''自由PK'
4. 强调'沙城争霸'等核心爽点
5. 展示极致打击感、全屏技能特效
6. 结尾强调'BOSS挑战掉落''快速升级成长'""",
        
        "DEFAULT": """【通用高转化特征】
买量文案必备要素：
1. 黄金前3秒必须吸睛（悬念/冲突/利益点）
2. 卖点清晰，USP 必须在脚本中明确传达
3. 内容风格匹配目标人群
4. 节奏紧凑，避免冗余镜头
5. 强力 CTA 引导转化（立即下载/限时福利）
6. 避免使用 HTML 标签，保持纯文本格式"""
    }
    
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
            
            # 使用 embedding 专用的 API Key
            api_key = config.get_embedding_api_key()
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
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
            
            # 使用 embedding 专用的 API Key
            api_key = config.get_embedding_api_key()
            
            headers = {
                "Authorization": f"Bearer {api_key}",
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
            
            # 使用 embedding 专用的 API Key
            api_key = config.get_embedding_api_key()
            
            client = OpenAI(
                api_key=api_key,
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
    
    def get_high_performing_traits(self, category: str) -> str:
        """
        获取指定品类的高转化广告特征
        
        Args:
            category: 游戏品类（SLG、MMO、休闲等）
            
        Returns:
            高转化特征描述字符串
        """
        # 尝试获取指定品类的特征，如果不存在则返回默认特征
        return self.HIGH_PERFORMING_TRAITS.get(
            category, 
            self.HIGH_PERFORMING_TRAITS["DEFAULT"]
        )
    
    def get_theme_traits(self, theme: str) -> dict:
        """
        获取指定题材的特征
        
        Args:
            theme: 游戏题材（魔幻、传奇、三国、武侠等）
            
        Returns:
            题材特征字典，包含核心特征和文案侧重点
        """
        return self.THEME_TRAITS.get(theme, {})
    
    def get_gameplay_traits(self, gameplay: str) -> dict:
        """
        获取指定玩法的特征
        
        Args:
            gameplay: 游戏玩法（休闲消除、网赚、放置挂机等）
            
        Returns:
            玩法特征字典，包含核心特征和文案侧重点
        """
        return self.GAMEPLAY_TRAITS.get(gameplay, {})
    
    def get_hybrid_gameplay_traits(self, hybrid_type: str) -> dict:
        """
        获取融合玩法的特征
        
        Args:
            hybrid_type: 融合玩法类型（SLG+副玩法、消除+X等）
            
        Returns:
            融合玩法特征字典
        """
        return self.HYBRID_GAMEPLAY_TRAITS.get(hybrid_type, {})
    
    def get_comprehensive_traits(
        self, 
        category: str, 
        theme: str = None, 
        gameplay: str = None
    ) -> str:
        """
        获取综合特征（品类 + 题材 + 玩法）
        
        Args:
            category: 游戏品类
            theme: 游戏题材（可选）
            gameplay: 游戏玩法（可选）
            
        Returns:
            综合特征描述字符串
        """
        parts = []
        
        # 1. 品类特征（必选）
        category_traits = self.get_high_performing_traits(category)
        parts.append(category_traits)
        
        # 2. 题材特征（可选）
        if theme:
            theme_data = self.get_theme_traits(theme)
            if theme_data:
                theme_text = f"\n\n【{theme}题材特征】\n"
                theme_text += f"核心特征：{theme_data.get('核心特征', '')}\n"
                theme_text += "文案侧重点：\n"
                for point in theme_data.get('文案侧重点', []):
                    theme_text += f"- {point}\n"
                parts.append(theme_text)
        
        # 3. 玩法特征（可选）
        if gameplay:
            gameplay_data = self.get_gameplay_traits(gameplay)
            if gameplay_data:
                gameplay_text = f"\n\n【{gameplay}玩法特征】\n"
                gameplay_text += f"核心特征：{gameplay_data.get('核心特征', '')}\n"
                gameplay_text += "文案侧重点：\n"
                for point in gameplay_data.get('文案侧重点', []):
                    gameplay_text += f"- {point}\n"
                parts.append(gameplay_text)
        
        return "".join(parts)
    
    def list_available_themes(self) -> list[str]:
        """获取所有可用的题材列表"""
        return list(self.THEME_TRAITS.keys())
    
    def list_available_gameplays(self) -> list[str]:
        """获取所有可用的玩法列表"""
        return list(self.GAMEPLAY_TRAITS.keys())
    
    def list_available_hybrid_gameplays(self) -> list[str]:
        """获取所有可用的融合玩法列表"""
        return list(self.HYBRID_GAMEPLAY_TRAITS.keys())
    
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
    
    def auto_ingest_script(
        self,
        raw_text: str
    ) -> tuple[bool, str, Optional[EnhancedScriptMetadata]]:
        """
        智能入库：自动分析文案并入库
        
        通过 LLM 自动提取元数据，根据品类确定存储路径，
        同时写入文件系统和向量数据库。
        
        Args:
            raw_text: 原始广告文案
            
        Returns:
            (success, message, metadata)
            - success: 是否成功
            - message: 结果消息或错误信息
            - metadata: 提取的元数据（成功时），失败时为 None
        """
        # 导入 prompts 模块
        from src.prompts import PromptManager
        
        # 检查 API 管理器
        if not self._api_manager:
            return False, "未配置 API 管理器", None
        
        # 检查输入
        if not raw_text or not raw_text.strip():
            return False, "输入文案不能为空", None
        
        # 格式化 AUTO_TAGGING_TEMPLATE
        prompt = PromptManager.get_auto_tagging_prompt(raw_text)
        
        # 调用 LLM API
        messages = [{"role": "user", "content": prompt}]
        success, response = self._api_manager.chat(messages)
        
        if not success:
            return False, f"AI 调用失败: {response}", None
        
        # 解析响应
        parse_success, result, raw_response = parse_auto_tag_response(response)
        
        if not parse_success:
            # result 是错误信息字符串
            error_msg = f"{result}"
            if raw_response:
                error_msg += f"\n原始响应: {raw_response[:500]}"
            return False, error_msg, None
        
        # result 是 EnhancedScriptMetadata
        metadata: EnhancedScriptMetadata = result
        
        # 根据 category 确定存储路径
        category = metadata.category
        
        # 生成唯一 ID
        script_id = str(uuid.uuid4())
        
        # 创建脚本对象（使用旧版 ScriptMetadata 以兼容现有存储结构）
        script_metadata = ScriptMetadata(
            game_name=metadata.game_name,
            source=metadata.source,
            archived_at=metadata.archived_at
        )
        
        script = Script(
            id=script_id,
            content=raw_text,
            category=category,
            metadata=script_metadata
        )
        
        # 保存到文件系统
        file_saved = self._save_script_file(script)
        if not file_saved:
            return False, "保存到文件系统失败", None
        
        # 同时保存增强元数据到单独的 JSON 文件
        try:
            category_path = self.scripts_path / category
            category_path.mkdir(parents=True, exist_ok=True)
            
            # 保存增强元数据
            enhanced_metadata_file = category_path / f"{script_id}_enhanced.json"
            with open(enhanced_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 增强元数据保存失败不影响主流程
            pass
        
        # 添加到向量数据库（如果可用）
        if self._use_vector_db:
            try:
                if self._use_faiss:
                    self._add_to_faiss(script)
                elif CHROMADB_AVAILABLE and self._client:
                    collection = self._get_collection(category)
                    if collection:
                        collection.add(
                            ids=[script_id],
                            documents=[raw_text],
                            metadatas=[{
                                "category": category,
                                "game_name": metadata.game_name,
                                "source": metadata.source,
                                "archived_at": metadata.archived_at
                            }]
                        )
            except Exception as e:
                # 向量数据库添加失败不影响主流程，只记录日志
                print(f"向量数据库添加失败: {e}")
        
        # 返回成功结果
        return True, f"已归档到 [{category}] 品类", metadata
    
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
