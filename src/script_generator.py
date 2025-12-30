"""
脚本生成工作流模块

负责广告脚本的生成工作流，包括 RAG 检索、初稿生成、评审和迭代修正。
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Generator, Optional

from src.api_manager import APIManager
from src.rag_system import RAGSystem, Script
from src.prompts import PromptManager


@dataclass
class GenerationInput:
    """生成输入数据类"""
    game_intro: str
    usp: str
    target_audience: str
    category: str
    theme: Optional[str] = None  # 游戏题材
    gameplay: Optional[str] = None  # 核心玩法
    
    def validate(self) -> tuple[bool, str]:
        """
        验证输入数据
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.game_intro or not self.game_intro.strip():
            return False, "游戏介绍不能为空"
        if not self.usp or not self.usp.strip():
            return False, "USP（独特卖点）不能为空"
        if not self.target_audience or not self.target_audience.strip():
            return False, "目标人群不能为空"
        if not self.category or not self.category.strip():
            return False, "游戏品类不能为空"
        return True, ""


@dataclass
class ScriptOutput:
    """脚本输出数据类 - 标准三栏表格格式"""
    storyboard: list[str] = field(default_factory=list)  # 分镜
    voiceover: list[str] = field(default_factory=list)   # 口播
    design_intent: list[str] = field(default_factory=list)  # 设计意图
    raw_content: str = ""  # 原始内容
    
    def is_valid(self) -> bool:
        """检查输出是否有效（三栏非空且长度相等）"""
        if not self.storyboard or not self.voiceover or not self.design_intent:
            return False
        return len(self.storyboard) == len(self.voiceover) == len(self.design_intent)
    
    def to_markdown_table(self) -> str:
        """转换为 Markdown 表格格式"""
        if not self.is_valid():
            return self.raw_content
        
        lines = ["| 分镜 | 口播 | 设计意图 |", "|------|------|----------|"]
        for i in range(len(self.storyboard)):
            lines.append(f"| {self.storyboard[i]} | {self.voiceover[i]} | {self.design_intent[i]} |")
        return "\n".join(lines)


@dataclass
class GenerationStep:
    """生成步骤状态"""
    step_name: str  # rag_search, draft, review, refine
    status: str     # pending, running, completed, failed
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


def _clean_html_tags(text: str) -> str:
    """
    清理文本中的 HTML 标签
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return text
    
    # 移除常见的 HTML 标签
    # <br>, <br/>, <br />, <p>, </p>, <div>, </div> 等
    cleaned = re.sub(r'<br\s*/?>', '；', text)  # 将 <br> 替换为分号
    cleaned = re.sub(r'</?p\s*/?>', '', cleaned)  # 移除 <p> 标签
    cleaned = re.sub(r'</?div\s*/?>', '', cleaned)  # 移除 <div> 标签
    cleaned = re.sub(r'</?span[^>]*>', '', cleaned)  # 移除 <span> 标签
    cleaned = re.sub(r'<[^>]+>', '', cleaned)  # 移除其他所有 HTML 标签
    
    # 清理多余的分号和空格
    cleaned = re.sub(r'；+', '；', cleaned)  # 合并连续分号
    cleaned = re.sub(r'^\s*；\s*', '', cleaned)  # 移除开头的分号
    cleaned = re.sub(r'\s*；\s*$', '', cleaned)  # 移除结尾的分号
    
    return cleaned.strip()


def parse_script_output(raw_script: str) -> ScriptOutput:
    """
    解析脚本为标准三栏格式
    
    支持多种格式：
    1. Markdown 表格格式
    2. 分隔符格式（使用 | 或 / 分隔）
    3. 标签格式（[分镜]...[口播]...[设计意图]...）
    
    Args:
        raw_script: 原始脚本文本
        
    Returns:
        ScriptOutput 对象
    """
    output = ScriptOutput(raw_content=raw_script)
    
    if not raw_script or not raw_script.strip():
        return output
    
    # 尝试解析 Markdown 表格格式
    table_result = _parse_markdown_table(raw_script)
    if table_result and table_result.is_valid():
        return table_result
    
    # 尝试解析分隔符格式
    delimiter_result = _parse_delimiter_format(raw_script)
    if delimiter_result and delimiter_result.is_valid():
        return delimiter_result
    
    # 尝试解析标签格式
    tag_result = _parse_tag_format(raw_script)
    if tag_result and tag_result.is_valid():
        return tag_result
    
    # 尝试解析编号列表格式
    numbered_result = _parse_numbered_format(raw_script)
    if numbered_result and numbered_result.is_valid():
        return numbered_result
    
    return output


def _parse_markdown_table(text: str) -> Optional[ScriptOutput]:
    """解析 Markdown 表格格式"""
    lines = text.strip().split('\n')
    
    # 查找表格开始位置（包含 | 的行）
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            # 跳过分隔行（只包含 |、-、: 和空格）
            if re.match(r'^[\|\-\:\s]+$', stripped):
                in_table = True
                continue
            if in_table or _is_table_header(stripped):
                in_table = True
                table_lines.append(stripped)
    
    if len(table_lines) < 2:  # 至少需要表头和一行数据
        return None
    
    # 解析表头，确定列顺序
    header = table_lines[0]
    header_cells = [cell.strip() for cell in header.split('|') if cell.strip()]
    
    # 查找各列索引
    storyboard_idx = -1
    voiceover_idx = -1
    design_idx = -1
    
    for i, cell in enumerate(header_cells):
        cell_lower = cell.lower()
        if '分镜' in cell or 'storyboard' in cell_lower or '画面' in cell:
            storyboard_idx = i
        elif '口播' in cell or 'voiceover' in cell_lower or '文案' in cell or '旁白' in cell:
            voiceover_idx = i
        elif '设计' in cell or '意图' in cell or 'design' in cell_lower or 'intent' in cell_lower:
            design_idx = i
    
    # 如果没有找到所有列，尝试按顺序假设
    if storyboard_idx == -1 or voiceover_idx == -1 or design_idx == -1:
        if len(header_cells) >= 3:
            storyboard_idx = 0
            voiceover_idx = 1
            design_idx = 2
        else:
            return None
    
    # 解析数据行
    storyboard = []
    voiceover = []
    design_intent = []
    
    for line in table_lines[1:]:
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if len(cells) >= 3:
            # 清理 HTML 标签
            storyboard.append(_clean_html_tags(cells[storyboard_idx] if storyboard_idx < len(cells) else ""))
            voiceover.append(_clean_html_tags(cells[voiceover_idx] if voiceover_idx < len(cells) else ""))
            design_intent.append(_clean_html_tags(cells[design_idx] if design_idx < len(cells) else ""))
    
    if not storyboard:
        return None
    
    return ScriptOutput(
        storyboard=storyboard,
        voiceover=voiceover,
        design_intent=design_intent,
        raw_content=text
    )


def _is_table_header(line: str) -> bool:
    """检查是否是表格表头行"""
    keywords = ['分镜', '口播', '设计', '画面', '文案', '意图', 'storyboard', 'voiceover', 'design']
    line_lower = line.lower()
    return any(kw in line_lower for kw in keywords)


def _parse_delimiter_format(text: str) -> Optional[ScriptOutput]:
    """解析分隔符格式（每行使用 | 或 / 分隔三栏）"""
    lines = text.strip().split('\n')
    
    storyboard = []
    voiceover = []
    design_intent = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 跳过表头行
        if _is_table_header(stripped):
            continue
        
        # 尝试使用 | 分隔
        if '|' in stripped:
            parts = [p.strip() for p in stripped.split('|') if p.strip()]
            if len(parts) >= 3:
                storyboard.append(_clean_html_tags(parts[0]))
                voiceover.append(_clean_html_tags(parts[1]))
                design_intent.append(_clean_html_tags(parts[2]))
                continue
        
        # 尝试使用 / 分隔
        if '/' in stripped:
            parts = [p.strip() for p in stripped.split('/') if p.strip()]
            if len(parts) >= 3:
                storyboard.append(_clean_html_tags(parts[0]))
                voiceover.append(_clean_html_tags(parts[1]))
                design_intent.append(_clean_html_tags(parts[2]))
    
    if not storyboard:
        return None
    
    return ScriptOutput(
        storyboard=storyboard,
        voiceover=voiceover,
        design_intent=design_intent,
        raw_content=text
    )


def _parse_tag_format(text: str) -> Optional[ScriptOutput]:
    """解析标签格式（[分镜]...[口播]...[设计意图]...）"""
    # 匹配各种标签格式
    storyboard_pattern = r'\[分镜\][:：]?\s*([^\[]+?)(?=\[|$)'
    voiceover_pattern = r'\[口播\][:：]?\s*([^\[]+?)(?=\[|$)'
    design_pattern = r'\[设计意图\][:：]?\s*([^\[]+?)(?=\[|$)'
    
    storyboard_matches = re.findall(storyboard_pattern, text, re.DOTALL)
    voiceover_matches = re.findall(voiceover_pattern, text, re.DOTALL)
    design_matches = re.findall(design_pattern, text, re.DOTALL)
    
    if not storyboard_matches or not voiceover_matches or not design_matches:
        return None
    
    # 清理匹配结果和 HTML 标签
    storyboard = [_clean_html_tags(m.strip()) for m in storyboard_matches if m.strip()]
    voiceover = [_clean_html_tags(m.strip()) for m in voiceover_matches if m.strip()]
    design_intent = [_clean_html_tags(m.strip()) for m in design_matches if m.strip()]
    
    # 确保长度一致
    min_len = min(len(storyboard), len(voiceover), len(design_intent))
    if min_len == 0:
        return None
    
    return ScriptOutput(
        storyboard=storyboard[:min_len],
        voiceover=voiceover[:min_len],
        design_intent=design_intent[:min_len],
        raw_content=text
    )


def _parse_numbered_format(text: str) -> Optional[ScriptOutput]:
    """解析编号列表格式"""
    # 匹配编号格式，如 "1. 分镜: xxx 口播: xxx 设计意图: xxx"
    pattern = r'(\d+)[\.、]\s*(?:分镜[:：]?\s*)?(.+?)(?:口播[:：]?\s*)(.+?)(?:设计意图[:：]?\s*)(.+?)(?=\d+[\.、]|$)'
    
    matches = re.findall(pattern, text, re.DOTALL)
    
    if not matches:
        return None
    
    storyboard = []
    voiceover = []
    design_intent = []
    
    for match in matches:
        if len(match) >= 4:
            storyboard.append(_clean_html_tags(match[1].strip()))
            voiceover.append(_clean_html_tags(match[2].strip()))
            design_intent.append(_clean_html_tags(match[3].strip()))
    
    if not storyboard:
        return None
    
    return ScriptOutput(
        storyboard=storyboard,
        voiceover=voiceover,
        design_intent=design_intent,
        raw_content=text
    )


class ScriptGenerator:
    """脚本生成器"""
    
    def __init__(
        self,
        api_manager: APIManager,
        rag_system: RAGSystem,
        review_api_manager: Optional[APIManager] = None
    ):
        """
        初始化脚本生成器
        
        Args:
            api_manager: 生成专用 API 管理器
            rag_system: RAG 系统实例
            review_api_manager: 评审专用 API 管理器（可选，默认使用 api_manager）
        """
        self.api_manager = api_manager
        self.rag_system = rag_system
        # 双模型架构：生成和评审使用独立的 API 管理器
        self.gen_api = api_manager
        self.rev_api = review_api_manager if review_api_manager else api_manager
    
    def get_model_info(self) -> dict:
        """
        获取当前使用的模型信息
        
        Returns:
            包含生成模型和评审模型信息的字典
        """
        gen_config = self.gen_api.load_config()
        rev_config = self.rev_api.load_config()
        
        return {
            "gen_model": gen_config.model_id if gen_config else "未配置",
            "gen_name": gen_config.name if gen_config else "未配置",
            "rev_model": rev_config.model_id if rev_config else "未配置",
            "rev_name": rev_config.name if rev_config else "未配置",
            "is_same_model": self.gen_api is self.rev_api
        }
    
    def generate(
        self,
        input_data: GenerationInput,
        on_step: Optional[Callable[[GenerationStep], None]] = None
    ) -> Generator[str, None, ScriptOutput]:
        """
        执行完整生成工作流，支持流式输出
        
        流程: RAG检索 -> 生成初稿 -> 评审 -> 迭代修正
        
        Args:
            input_data: 生成输入数据
            on_step: 步骤回调函数
            
        Yields:
            生成的文本片段
            
        Returns:
            最终的 ScriptOutput 对象
        """
        # 验证输入
        is_valid, error_msg = input_data.validate()
        if not is_valid:
            yield f"[错误] {error_msg}"
            return ScriptOutput(raw_content=f"[错误] {error_msg}")
        
        # Step 1: RAG 检索
        if on_step:
            on_step(GenerationStep(
                step_name="rag_search",
                status="running",
                content="正在检索同品类参考脚本..."
            ))
        
        yield "📚 正在检索同品类参考脚本...\n\n"
        
        references = self._search_references(input_data)
        references_text = self._format_references(references)
        
        if on_step:
            on_step(GenerationStep(
                step_name="rag_search",
                status="completed",
                content=f"找到 {len(references)} 个参考脚本"
            ))
        
        yield f"✅ 找到 {len(references)} 个参考脚本\n\n"
        
        # Step 2: 生成初稿
        if on_step:
            on_step(GenerationStep(
                step_name="draft",
                status="running",
                content="正在生成脚本初稿..."
            ))
        
        yield "✍️ 正在生成脚本初稿...\n\n"
        
        draft_content = ""
        for chunk in self._generate_draft(input_data, references_text):
            draft_content += chunk
            yield chunk
        
        if on_step:
            on_step(GenerationStep(
                step_name="draft",
                status="completed",
                content=draft_content
            ))
        
        yield "\n\n"
        
        # Step 3: 评审 (流式)
        if on_step:
            on_step(GenerationStep(
                step_name="review",
                status="running",
                content="正在评审脚本..."
            ))
        
        yield "🔍 正在评审脚本...\n\n"
        
        review_feedback = ""
        for chunk in self._review_script(input_data, draft_content):
            review_feedback += chunk
            yield f"[REVIEW]{chunk}"  # 带标记的评审内容
        
        if on_step:
            on_step(GenerationStep(
                step_name="review",
                status="completed",
                content=review_feedback
            ))
        
        yield "\n\n"
        
        # Step 4: 迭代修正
        if on_step:
            on_step(GenerationStep(
                step_name="refine",
                status="running",
                content="正在根据评审意见修正脚本..."
            ))
        
        yield "🔧 正在根据评审意见修正脚本...\n\n"
        
        final_content = ""
        for chunk in self._refine_script(input_data, draft_content, review_feedback):
            final_content += chunk
            yield chunk
        
        if on_step:
            on_step(GenerationStep(
                step_name="refine",
                status="completed",
                content=final_content
            ))
        
        yield "\n\n✅ 脚本生成完成！\n"
        
        # 解析最终输出
        output = parse_script_output(final_content)
        return output
    
    def _search_references(self, input_data: GenerationInput) -> list[Script]:
        """
        RAG 检索同品类爆款脚本
        
        Args:
            input_data: 生成输入数据
            
        Returns:
            相关脚本列表
        """
        try:
            # 构建查询文本
            query = f"{input_data.game_intro} {input_data.usp} {input_data.target_audience}"
            
            # 检索同品类脚本
            scripts = self.rag_system.search(
                query=query,
                category=input_data.category,
                top_k=3
            )
            
            return scripts
        except Exception:
            return []
    
    def _format_references(self, references: list[Script]) -> str:
        """格式化参考脚本"""
        if not references:
            return "（暂无同品类参考脚本）"
        
        formatted = []
        for i, script in enumerate(references, 1):
            formatted.append(f"### 参考脚本 {i}\n{script.content}\n")
        
        return "\n".join(formatted)
    
    def _generate_draft(
        self,
        input_data: GenerationInput,
        references_text: str
    ) -> Generator[str, None, None]:
        """
        生成脚本初稿
        
        Args:
            input_data: 生成输入数据
            references_text: 格式化的参考脚本文本
            
        Yields:
            生成的文本片段
        """
        prompt = PromptManager.get_draft_prompt(
            game_intro=input_data.game_intro,
            usp=input_data.usp,
            target_audience=input_data.target_audience,
            category=input_data.category,
            references=references_text
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        for chunk in self.api_manager.stream_chat(messages):
            yield chunk
    
    def _review_script(
        self, 
        input_data: GenerationInput, 
        script: str
    ) -> Generator[str, None, None]:
        """
        使用高级评审流程评审脚本 (流式版本)
        
        步骤:
        1. 获取 RAG 综合特征（品类 + 题材 + 玩法）
        2. 构建高级评审 Prompt
        3. 使用评审专用 API 流式发送请求
        
        Args:
            input_data: 生成输入数据
            script: 待评审的脚本
            
        Yields:
            评审内容片段
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Step 1: 获取 RAG 综合特征（品类 + 题材 + 玩法）
        rag_traits = None
        try:
            # 使用综合特征方法，整合品类、题材、玩法的特征
            rag_traits = self.rag_system.get_comprehensive_traits(
                category=input_data.category,
                theme=input_data.theme,
                gameplay=input_data.gameplay
            )
            logger.info(f"获取 RAG 综合特征成功，品类: {input_data.category}, 题材: {input_data.theme}, 玩法: {input_data.gameplay}")
            logger.debug(f"RAG 特征内容: {rag_traits}")
        except Exception as e:
            # RAG 获取失败时使用默认特征
            logger.warning(f"RAG 特征获取失败，使用默认特征: {e}")
            rag_traits = self.rag_system.HIGH_PERFORMING_TRAITS.get("DEFAULT", "")
        
        # Step 2: 构建评审 Prompt（传入 rag_traits 参数）
        prompt = PromptManager.get_review_prompt(
            game_intro=input_data.game_intro,
            usp=input_data.usp,
            target_audience=input_data.target_audience,
            category=input_data.category,
            script=script,
            rag_traits=rag_traits,
            use_advanced=True
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        # Step 3: 使用评审专用 API（rev_api）流式发送请求
        rev_config = self.rev_api.load_config()
        if rev_config:
            logger.info(f"使用评审模型: {rev_config.model_id} ({rev_config.name})")
        
        try:
            for chunk in self.rev_api.stream_chat(messages):
                yield chunk
        except Exception as e:
            yield f"[错误] 评审过程中断: {str(e)}"
    
    def _refine_script(
        self,
        input_data: GenerationInput,
        script: str,
        review_feedback: str
    ) -> Generator[str, None, None]:
        """
        根据评审意见迭代修正脚本
        
        Args:
            input_data: 生成输入数据
            script: 原始脚本
            review_feedback: 评审意见
            
        Yields:
            生成的文本片段
        """
        prompt = PromptManager.get_refine_prompt(
            game_intro=input_data.game_intro,
            usp=input_data.usp,
            target_audience=input_data.target_audience,
            category=input_data.category,
            script=script,
            review_feedback=review_feedback
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        for chunk in self.api_manager.stream_chat(messages):
            yield chunk
    
    def generate_simple(
        self,
        input_data: GenerationInput,
        use_rag: bool = True,
        use_review: bool = True
    ) -> tuple[bool, ScriptOutput]:
        """
        简化的生成方法（非流式）
        
        Args:
            input_data: 生成输入数据
            use_rag: 是否使用 RAG 检索
            use_review: 是否进行评审和修正
            
        Returns:
            (成功标志, ScriptOutput 对象)
        """
        # 验证输入
        is_valid, error_msg = input_data.validate()
        if not is_valid:
            return False, ScriptOutput(raw_content=f"[错误] {error_msg}")
        
        # RAG 检索
        references_text = "（暂无同品类参考脚本）"
        if use_rag:
            references = self._search_references(input_data)
            references_text = self._format_references(references)
        
        # 生成初稿
        draft_content = ""
        for chunk in self._generate_draft(input_data, references_text):
            draft_content += chunk
        
        if not draft_content or draft_content.startswith("[错误]"):
            return False, ScriptOutput(raw_content=draft_content)
        
        # 评审和修正
        if use_review:
            # 收集流式评审内容
            review_feedback = ""
            for chunk in self._review_script(input_data, draft_content):
                review_feedback += chunk
            
            final_content = ""
            for chunk in self._refine_script(input_data, draft_content, review_feedback):
                final_content += chunk
            
            if final_content and not final_content.startswith("[错误]"):
                output = parse_script_output(final_content)
                return True, output
        
        # 如果不评审或评审失败，返回初稿
        output = parse_script_output(draft_content)
        return True, output
