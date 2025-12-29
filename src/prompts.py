"""
Prompt 模板模块

定义脚本生成、评审、修正的 Prompt 模板。
支持模板变量替换和多语言扩展。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PromptTemplate:
    """Prompt 模板基类"""
    template: str
    name: str
    description: str
    
    def format(self, **kwargs) -> str:
        """
        格式化模板，替换变量
        
        Args:
            **kwargs: 模板变量
            
        Returns:
            格式化后的 Prompt 字符串
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板 '{self.name}' 缺少必要变量: {e}")


# ==================== 脚本生成 Prompt ====================

DRAFT_GENERATION_TEMPLATE = """你是一位专业的游戏广告创意专家，擅长创作吸引人的信息流广告脚本。

## 任务
根据以下游戏信息，创作一个信息流广告脚本。脚本需要以标准三栏表格格式输出。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}
- **游戏品类：** {category}

## 参考脚本
以下是同品类的优秀脚本供参考：
{references}

## 创作要求
1. **开头吸睛**：前3秒必须抓住用户注意力，可使用悬念、冲突、利益点等手法
2. **卖点突出**：USP 必须在脚本中清晰传达，让用户记住核心卖点
3. **目标匹配**：内容风格和表达方式要符合目标人群的喜好和习惯
4. **节奏紧凑**：每个分镜都要有明确目的，避免冗余内容
5. **行动号召**：结尾要有明确的转化引导，如"立即下载"、"限时福利"等

## 输出格式
请以 Markdown 表格格式输出脚本，包含以下三栏：
1. **分镜**：描述画面内容，包括场景、角色、动作等
2. **口播**：配音文案，要口语化、有感染力
3. **设计意图**：该分镜的创意目的和预期效果

示例格式：
| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述1 | 配音文案1 | 创意目的1 |
| 画面描述2 | 配音文案2 | 创意目的2 |

请创作 5-8 个分镜的完整脚本，确保整体时长控制在 15-30 秒。"""

DRAFT_PROMPT = PromptTemplate(
    template=DRAFT_GENERATION_TEMPLATE,
    name="draft_generation",
    description="脚本初稿生成 Prompt"
)


# ==================== 脚本评审 Prompt ====================

REVIEW_TEMPLATE = """你是一位资深的广告创意总监，拥有丰富的游戏广告评审经验。

## 任务
评审以下游戏广告脚本，并给出专业、具体的修改建议。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}
- **游戏品类：** {category}

## 待评审脚本
{script}

## 评审维度

### 1. 创意吸引力（权重：25%）
- 开头是否能在3秒内抓住用户注意力？
- 是否使用了有效的 Hook（悬念、冲突、利益点）？
- 整体创意是否新颖、有记忆点？

### 2. 卖点传达（权重：25%）
- USP 是否清晰、准确地传达？
- 卖点呈现方式是否有说服力？
- 用户能否快速理解游戏的核心价值？

### 3. 目标匹配（权重：20%）
- 内容风格是否符合目标人群的喜好？
- 语言表达是否贴近目标用户？
- 场景设置是否能引起目标用户共鸣？

### 4. 节奏把控（权重：15%）
- 分镜节奏是否合理？
- 信息密度是否适中？
- 整体时长是否符合信息流广告规范？

### 5. 行动号召（权重：15%）
- 是否有明确的转化引导？
- CTA（Call to Action）是否有吸引力？
- 结尾是否给用户留下行动动机？

## 输出要求
请按以下格式输出评审结果：

### 总体评价
（用1-2句话概括脚本的整体质量，给出评分：优秀/良好/一般/需改进）

### 亮点
（列出脚本的2-3个优点）

### 改进建议
（针对每个需要改进的点，给出具体、可操作的修改建议）

1. **[问题点1]**
   - 当前问题：...
   - 修改建议：...

2. **[问题点2]**
   - 当前问题：...
   - 修改建议：...

### 优先级排序
（将改进建议按重要性排序，标注"必须修改"或"建议修改"）"""

REVIEW_PROMPT = PromptTemplate(
    template=REVIEW_TEMPLATE,
    name="script_review",
    description="脚本评审 Prompt"
)


# ==================== 脚本修正 Prompt ====================

REFINE_TEMPLATE = """你是一位专业的游戏广告创意专家，需要根据评审意见修改脚本。

## 任务
根据评审意见修改以下广告脚本，确保修改后的脚本质量更高。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}
- **游戏品类：** {category}

## 原始脚本
{script}

## 评审意见
{review_feedback}

## 修改要求
1. **针对性修改**：逐一解决评审意见中提出的问题
2. **保留优点**：保持原脚本中的亮点和优秀创意
3. **整体优化**：在修改的同时，提升脚本的整体质量
4. **格式规范**：确保输出格式符合标准三栏表格

## 输出格式
请以 Markdown 表格格式输出修改后的完整脚本：

| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述 | 配音文案 | 创意目的 |

请输出完整的修改后脚本，不要省略任何分镜。"""

REFINE_PROMPT = PromptTemplate(
    template=REFINE_TEMPLATE,
    name="script_refine",
    description="脚本修正 Prompt"
)


# ==================== 快速生成 Prompt（无评审） ====================

QUICK_GENERATION_TEMPLATE = """你是一位专业的游戏广告创意专家。

## 任务
快速创作一个游戏信息流广告脚本。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}
- **游戏品类：** {category}

## 输出要求
直接输出 Markdown 表格格式的脚本，包含 5-8 个分镜：

| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述 | 配音文案 | 创意目的 |

要求：
- 开头3秒抓住注意力
- 清晰传达 USP
- 结尾有行动号召"""

QUICK_GENERATION_PROMPT = PromptTemplate(
    template=QUICK_GENERATION_TEMPLATE,
    name="quick_generation",
    description="快速脚本生成 Prompt（无评审流程）"
)


# ==================== 品类特化 Prompt ====================

SLG_SPECIFIC_TEMPLATE = """你是一位专业的 SLG（策略类）游戏广告创意专家。

## 任务
为以下 SLG 游戏创作信息流广告脚本。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}

## SLG 广告创作要点
1. **策略深度**：展示游戏的策略性和智力挑战
2. **成就感**：强调征服、统一、称霸的成就感
3. **社交元素**：突出联盟、国战、外交等社交玩法
4. **数值成长**：展示角色/势力的成长和强化
5. **史诗感**：营造宏大的世界观和史诗氛围

## 参考脚本
{references}

## 输出格式
| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述 | 配音文案 | 创意目的 |

请创作 5-8 个分镜的完整脚本。"""

SLG_PROMPT = PromptTemplate(
    template=SLG_SPECIFIC_TEMPLATE,
    name="slg_generation",
    description="SLG 品类特化脚本生成 Prompt"
)


MMO_SPECIFIC_TEMPLATE = """你是一位专业的 MMO（大型多人在线）游戏广告创意专家。

## 任务
为以下 MMO 游戏创作信息流广告脚本。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}

## MMO 广告创作要点
1. **社交体验**：强调与好友组队、公会活动等社交乐趣
2. **角色成长**：展示角色的成长、转职、装备等
3. **世界探索**：展现广阔的游戏世界和丰富的内容
4. **战斗体验**：突出爽快的战斗和技能特效
5. **情感连接**：营造归属感和情感共鸣

## 参考脚本
{references}

## 输出格式
| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述 | 配音文案 | 创意目的 |

请创作 5-8 个分镜的完整脚本。"""

MMO_PROMPT = PromptTemplate(
    template=MMO_SPECIFIC_TEMPLATE,
    name="mmo_generation",
    description="MMO 品类特化脚本生成 Prompt"
)


CASUAL_SPECIFIC_TEMPLATE = """你是一位专业的休闲游戏广告创意专家。

## 任务
为以下休闲游戏创作信息流广告脚本。

## 游戏信息
- **游戏介绍：** {game_intro}
- **独特卖点（USP）：** {usp}
- **目标人群：** {target_audience}

## 休闲游戏广告创作要点
1. **简单易上手**：强调游戏的简单性和易玩性
2. **解压放松**：突出游戏的休闲解压属性
3. **即时满足**：展示快速获得成就感的体验
4. **碎片时间**：强调随时随地可玩的便利性
5. **趣味性**：展现游戏的趣味和创意玩法

## 参考脚本
{references}

## 输出格式
| 分镜 | 口播 | 设计意图 |
|------|------|----------|
| 画面描述 | 配音文案 | 创意目的 |

请创作 5-8 个分镜的完整脚本。"""

CASUAL_PROMPT = PromptTemplate(
    template=CASUAL_SPECIFIC_TEMPLATE,
    name="casual_generation",
    description="休闲游戏品类特化脚本生成 Prompt"
)


# ==================== Prompt 管理器 ====================

class PromptManager:
    """Prompt 模板管理器"""
    
    # 默认 Prompt 模板
    DEFAULT_PROMPTS = {
        "draft": DRAFT_PROMPT,
        "review": REVIEW_PROMPT,
        "refine": REFINE_PROMPT,
        "quick": QUICK_GENERATION_PROMPT,
    }
    
    # 品类特化 Prompt
    CATEGORY_PROMPTS = {
        "SLG": SLG_PROMPT,
        "MMO": MMO_PROMPT,
        "休闲": CASUAL_PROMPT,
    }
    
    # API 管理器引用（用于加载自定义提示词）
    _api_manager = None
    
    @classmethod
    def set_api_manager(cls, api_manager):
        """设置 API 管理器引用"""
        cls._api_manager = api_manager
    
    @classmethod
    def get_custom_prompt(cls, prompt_name: str) -> Optional[str]:
        """获取自定义提示词"""
        if cls._api_manager:
            return cls._api_manager.get_prompt(prompt_name)
        return None
    
    @classmethod
    def get_default_template(cls, prompt_name: str) -> str:
        """获取默认提示词模板"""
        if prompt_name in cls.DEFAULT_PROMPTS:
            return cls.DEFAULT_PROMPTS[prompt_name].template
        return ""
    
    @classmethod
    def get_draft_prompt(
        cls,
        game_intro: str,
        usp: str,
        target_audience: str,
        category: str,
        references: str = "（暂无同品类参考脚本）"
    ) -> str:
        """
        获取脚本生成 Prompt
        
        Args:
            game_intro: 游戏介绍
            usp: 独特卖点
            target_audience: 目标人群
            category: 游戏品类
            references: 参考脚本文本
            
        Returns:
            格式化后的 Prompt
        """
        # 首先检查是否有自定义提示词
        custom_prompt = cls.get_custom_prompt("draft")
        if custom_prompt:
            try:
                return custom_prompt.format(
                    game_intro=game_intro,
                    usp=usp,
                    target_audience=target_audience,
                    category=category,
                    references=references
                )
            except KeyError:
                pass  # 格式化失败，使用默认
        
        # 尝试使用品类特化 Prompt
        if category in cls.CATEGORY_PROMPTS:
            prompt_template = cls.CATEGORY_PROMPTS[category]
            return prompt_template.format(
                game_intro=game_intro,
                usp=usp,
                target_audience=target_audience,
                references=references
            )
        
        # 使用默认 Prompt
        return cls.DEFAULT_PROMPTS["draft"].format(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category,
            references=references
        )
    
    @classmethod
    def get_review_prompt(
        cls,
        game_intro: str,
        usp: str,
        target_audience: str,
        category: str,
        script: str
    ) -> str:
        """
        获取脚本评审 Prompt
        
        Args:
            game_intro: 游戏介绍
            usp: 独特卖点
            target_audience: 目标人群
            category: 游戏品类
            script: 待评审脚本
            
        Returns:
            格式化后的 Prompt
        """
        # 首先检查是否有自定义提示词
        custom_prompt = cls.get_custom_prompt("review")
        if custom_prompt:
            try:
                return custom_prompt.format(
                    game_intro=game_intro,
                    usp=usp,
                    target_audience=target_audience,
                    category=category,
                    script=script
                )
            except KeyError:
                pass  # 格式化失败，使用默认
        
        return cls.DEFAULT_PROMPTS["review"].format(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category,
            script=script
        )
    
    @classmethod
    def get_refine_prompt(
        cls,
        game_intro: str,
        usp: str,
        target_audience: str,
        category: str,
        script: str,
        review_feedback: str
    ) -> str:
        """
        获取脚本修正 Prompt
        
        Args:
            game_intro: 游戏介绍
            usp: 独特卖点
            target_audience: 目标人群
            category: 游戏品类
            script: 原始脚本
            review_feedback: 评审意见
            
        Returns:
            格式化后的 Prompt
        """
        # 首先检查是否有自定义提示词
        custom_prompt = cls.get_custom_prompt("refine")
        if custom_prompt:
            try:
                return custom_prompt.format(
                    game_intro=game_intro,
                    usp=usp,
                    target_audience=target_audience,
                    category=category,
                    script=script,
                    review_feedback=review_feedback
                )
            except KeyError:
                pass  # 格式化失败，使用默认
        
        return cls.DEFAULT_PROMPTS["refine"].format(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category,
            script=script,
            review_feedback=review_feedback
        )
    
    @classmethod
    def get_quick_prompt(
        cls,
        game_intro: str,
        usp: str,
        target_audience: str,
        category: str
    ) -> str:
        """
        获取快速生成 Prompt（无评审流程）
        
        Args:
            game_intro: 游戏介绍
            usp: 独特卖点
            target_audience: 目标人群
            category: 游戏品类
            
        Returns:
            格式化后的 Prompt
        """
        return cls.DEFAULT_PROMPTS["quick"].format(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category
        )
    
    @classmethod
    def list_available_prompts(cls) -> dict:
        """
        列出所有可用的 Prompt 模板
        
        Returns:
            Prompt 模板字典 {名称: 描述}
        """
        prompts = {}
        for name, prompt in cls.DEFAULT_PROMPTS.items():
            prompts[name] = prompt.description
        for category, prompt in cls.CATEGORY_PROMPTS.items():
            prompts[f"category_{category}"] = prompt.description
        return prompts
