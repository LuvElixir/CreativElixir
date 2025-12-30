"""
核心逻辑层验证测试

验证双模型评审架构的核心组件：
- RAG 高转化特征检索
- 高级评审 Prompt 模板
- ScriptGenerator 双模型支持
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.rag_system import RAGSystem
from src.prompts import PromptManager, ADVANCED_REVIEW_PROMPT
from src.script_generator import ScriptGenerator


class TestRAGHighPerformingTraits:
    """RAG 高转化特征检索测试 - Property 3"""
    
    def test_slg_traits_returns_specific_content(self):
        """Feature: dual-model-review-architecture, Property 3: RAG 特征检索完整性 - SLG"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("SLG")
        
        assert traits is not None
        assert len(traits) > 0
        assert "战力" in traits
        assert "以弱胜强" in traits
        assert "连抽" in traits
    
    def test_mmo_traits_returns_specific_content(self):
        """Feature: dual-model-review-architecture, Property 3: RAG 特征检索完整性 - MMO"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("MMO")
        
        assert traits is not None
        assert len(traits) > 0
        assert "捏脸" in traits
        assert "自由交易" in traits or "回收" in traits
    
    def test_default_traits_for_unknown_category(self):
        """Feature: dual-model-review-architecture, Property 3: RAG 特征检索完整性 - 未知品类"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("未知品类")
        
        assert traits is not None
        assert len(traits) > 0
        assert "前3秒" in traits
        assert "卖点" in traits
        assert "CTA" in traits
    
    def test_casual_uses_default_traits(self):
        """Feature: dual-model-review-architecture, Property 3: RAG 特征检索完整性 - 休闲"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("休闲")
        
        assert traits is not None
        assert len(traits) > 0
        # 休闲品类使用默认特征
        assert "前3秒" in traits


class TestAdvancedReviewPrompt:
    """高级评审 Prompt 模板测试 - Property 4"""
    
    def test_advanced_review_template_exists(self):
        """验证 ADVANCED_REVIEW_TEMPLATE 存在"""
        assert ADVANCED_REVIEW_PROMPT is not None
        assert ADVANCED_REVIEW_PROMPT.template is not None
        assert len(ADVANCED_REVIEW_PROMPT.template) > 0
    
    def test_template_contains_required_placeholders(self):
        """验证模板包含必要占位符"""
        template = ADVANCED_REVIEW_PROMPT.template
        
        assert "{game_intro}" in template
        assert "{usp}" in template
        assert "{target_audience}" in template
        assert "{category}" in template
        assert "{script}" in template
        assert "{rag_traits}" in template
    
    def test_template_contains_three_roles(self):
        """验证模板包含三个评审角色"""
        template = ADVANCED_REVIEW_PROMPT.template
        
        assert "投放投手" in template or "User Acquisition" in template
        assert "硬核" in template or "Hardcore Gamer" in template
        assert "产品经理" in template or "Product Manager" in template
    
    def test_rag_traits_injection(self):
        """Feature: dual-model-review-architecture, Property 4: Prompt 模板 RAG 特征注入"""
        test_traits = "测试特征内容_12345_唯一标识"
        
        prompt = PromptManager.get_review_prompt(
            game_intro="测试游戏介绍",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG",
            script="测试脚本内容",
            rag_traits=test_traits,
            use_advanced=True
        )
        
        assert test_traits in prompt
    
    def test_advanced_review_registered_in_default_prompts(self):
        """验证 advanced_review 已注册到 DEFAULT_PROMPTS"""
        assert "advanced_review" in PromptManager.DEFAULT_PROMPTS
        assert PromptManager.DEFAULT_PROMPTS["advanced_review"] == ADVANCED_REVIEW_PROMPT


class TestScriptGeneratorDualModel:
    """ScriptGenerator 双模型支持测试 - Property 1 & 2"""
    
    def test_dual_api_manager_separation(self):
        """Feature: dual-model-review-architecture, Property 1: 双 API 管理器正确分离"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        assert generator.gen_api is gen_api
        assert generator.rev_api is rev_api
        assert generator.gen_api is not generator.rev_api
    
    def test_default_review_api_fallback(self):
        """Feature: dual-model-review-architecture, Property 2: 默认评审 API 回退"""
        gen_api = Mock()
        rag_system = Mock()
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=None
        )
        
        assert generator.rev_api is generator.gen_api
    
    def test_get_model_info_returns_correct_structure(self):
        """验证 get_model_info 返回正确的结构"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 模拟 load_config 返回
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        model_info = generator.get_model_info()
        
        assert "gen_model" in model_info
        assert "gen_name" in model_info
        assert "rev_model" in model_info
        assert "rev_name" in model_info
        assert "is_same_model" in model_info
        assert model_info["gen_model"] == "gpt-3.5-turbo"
        assert model_info["rev_model"] == "gpt-4"
        assert model_info["is_same_model"] is False
    
    def test_same_model_when_no_review_api(self):
        """验证未提供评审 API 时 is_same_model 为 True"""
        gen_api = Mock()
        rag_system = Mock()
        
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=None
        )
        
        model_info = generator.get_model_info()
        
        assert model_info["is_same_model"] is True


class TestReviewScriptIntegration:
    """评审流程集成测试"""
    
    def test_review_uses_rev_api(self):
        """验证评审流程使用 rev_api"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 设置 RAG 返回
        rag_system.get_high_performing_traits.return_value = "测试特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        # 设置 rev_api 返回
        rev_api.chat.return_value = (True, "评审结果")
        rev_api.load_config.return_value = Mock(model_id="gpt-4", name="评审模型")
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        from src.script_generator import GenerationInput
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        result = generator._review_script(input_data, "测试脚本")
        
        # 验证使用了 rev_api 而不是 gen_api
        rev_api.chat.assert_called_once()
        gen_api.chat.assert_not_called()
        
        # 验证调用了 RAG 特征检索
        rag_system.get_high_performing_traits.assert_called_once_with("SLG")
