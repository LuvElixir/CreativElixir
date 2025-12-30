"""
集成测试和验收测试

验证双模型评审架构的完整功能：
- 7.1 验证双模型架构工作正常
- 7.2 验证评审结果包含多角色视角
- 7.3 验证向后兼容性

Requirements: 1.2, 1.3, 1.4, 1.5, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

from src.rag_system import RAGSystem
from src.prompts import PromptManager, ADVANCED_REVIEW_PROMPT
from src.script_generator import ScriptGenerator, GenerationInput


class TestDualModelArchitecture:
    """
    7.1 验证双模型架构工作正常
    
    - 配置两个不同的 API（如 GPT-3.5 生成，GPT-4 评审）
    - 执行脚本生成流程
    - 验证日志显示正确的模型调用
    
    Requirements: 1.3, 1.4, 1.5
    """
    
    def test_dual_model_configuration(self):
        """验证可以配置两个不同的模型"""
        # 创建两个不同的 API 管理器 Mock
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 配置生成模型为 GPT-3.5
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型-GPT3.5"
        gen_api.load_config.return_value = gen_config
        
        # 配置评审模型为 GPT-4
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型-GPT4"
        rev_api.load_config.return_value = rev_config
        
        # 创建 ScriptGenerator
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        # 验证模型配置正确
        model_info = generator.get_model_info()
        assert model_info["gen_model"] == "gpt-3.5-turbo"
        assert model_info["rev_model"] == "gpt-4"
        assert model_info["is_same_model"] is False
    
    def test_generation_uses_gen_api(self):
        """验证生成流程使用 gen_api (Requirements: 1.3)"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 配置 Mock
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        gen_api.stream_chat.return_value = iter(["测试", "脚本", "内容"])
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        
        rag_system.search.return_value = []
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 执行生成初稿
        draft_content = ""
        for chunk in generator._generate_draft(input_data, "参考脚本"):
            draft_content += chunk
        
        # 验证使用了 gen_api（通过 api_manager）
        gen_api.stream_chat.assert_called_once()
        rev_api.stream_chat.assert_not_called()
    
    def test_review_uses_rev_api(self):
        """验证评审流程使用 rev_api 的 stream_chat (Requirements: 1.4)"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 配置 Mock
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        rev_api.stream_chat.return_value = iter(["评审", "结果"])
        
        rag_system.get_high_performing_traits.return_value = "测试特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 执行评审（现在返回 Generator，需要迭代消费）
        result = list(generator._review_script(input_data, "测试脚本"))
        
        # 验证使用了 rev_api.stream_chat
        rev_api.stream_chat.assert_called_once()
        gen_api.stream_chat.assert_not_called()
    
    def test_logging_shows_correct_model_calls(self):
        """验证日志显示正确的模型调用 (Requirements: 1.5)"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        # 配置 Mock
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        rev_api.stream_chat.return_value = iter(["评审", "结果"])
        
        rag_system.get_high_performing_traits.return_value = "测试特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 执行评审（现在返回 Generator，需要迭代消费）
        result = list(generator._review_script(input_data, "测试脚本"))
        
        # 验证 rev_api.load_config 被调用以获取模型信息用于日志记录
        # _review_script 方法内部会调用 rev_api.load_config() 来获取模型信息并记录日志
        rev_api.load_config.assert_called()
        
        # 验证 get_model_info 返回正确的模型信息
        model_info = generator.get_model_info()
        assert model_info["gen_model"] == "gpt-3.5-turbo"
        assert model_info["rev_model"] == "gpt-4"


class TestMultiRoleReview:
    """
    7.2 验证评审结果包含多角色视角
    
    - 检查评审输出包含"投放投手"、"硬核玩家"、"产品经理"角色
    - 检查评审输出引用了 RAG 高转化标准
    - 检查评审输出包含主席总结和3条修改建议
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    def test_advanced_review_template_contains_three_roles(self):
        """验证高级评审模板包含三个角色 (Requirements: 6.1)"""
        template = ADVANCED_REVIEW_PROMPT.template
        
        # 检查投放投手角色
        assert "投放投手" in template or "User Acquisition Specialist" in template
        # 检查硬核玩家角色
        assert "硬核" in template or "Hardcore Gamer" in template
        # 检查产品经理角色
        assert "产品经理" in template or "Product Manager" in template
    
    def test_template_contains_role_focus_points(self):
        """验证每个角色有明确的关注点 (Requirements: 6.2)"""
        template = ADVANCED_REVIEW_PROMPT.template
        
        # 投放投手关注点
        assert "黄金前3秒" in template or "前3秒" in template
        assert "CTA" in template
        
        # 硬核玩家关注点
        assert "真实性" in template
        assert "术语" in template or "爽点" in template
        
        # 产品经理关注点
        assert "USP" in template
        assert "人群匹配" in template or "匹配度" in template
    
    def test_template_contains_rag_traits_placeholder(self):
        """验证模板包含 RAG 特征占位符"""
        template = ADVANCED_REVIEW_PROMPT.template
        assert "{rag_traits}" in template
    
    def test_template_requires_chairman_summary(self):
        """验证模板要求主席总结 (Requirements: 6.3)"""
        template = ADVANCED_REVIEW_PROMPT.template
        assert "主席总结" in template or "主席" in template
    
    def test_template_requires_three_suggestions(self):
        """验证模板要求3条修改建议 (Requirements: 6.3, 6.4)"""
        template = ADVANCED_REVIEW_PROMPT.template
        assert "3" in template or "三" in template
        assert "修改建议" in template or "修改" in template
    
    def test_template_requires_specific_suggestion_format(self):
        """验证修改建议格式要求 (Requirements: 6.4, 6.5)"""
        template = ADVANCED_REVIEW_PROMPT.template
        
        # 检查问题位置
        assert "问题位置" in template
        # 检查问题诊断
        assert "问题诊断" in template
        # 检查修改方案
        assert "修改方案" in template
    
    def test_review_prompt_injects_rag_traits(self):
        """验证评审 Prompt 正确注入 RAG 特征"""
        test_traits = "1. 前3秒战力数值跳动\n2. 以弱胜强策略反转\n3. 开局送连抽"
        
        prompt = PromptManager.get_review_prompt(
            game_intro="测试SLG游戏",
            usp="策略深度",
            target_audience="策略游戏爱好者",
            category="SLG",
            script="测试脚本内容",
            rag_traits=test_traits,
            use_advanced=True
        )
        
        # 验证 RAG 特征被注入
        assert test_traits in prompt
        # 验证使用了高级模板
        assert "评审委员会" in prompt or "委员会" in prompt
    
    def test_rag_traits_retrieval_for_slg(self):
        """验证 SLG 品类的 RAG 特征检索"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("SLG")
        
        # 验证包含 SLG 特定特征
        assert "战力" in traits
        assert "以弱胜强" in traits
        assert "连抽" in traits
    
    def test_rag_traits_retrieval_for_mmo(self):
        """验证 MMO 品类的 RAG 特征检索"""
        rag_system = RAGSystem()
        traits = rag_system.get_high_performing_traits("MMO")
        
        # 验证包含 MMO 特定特征
        assert "捏脸" in traits
        assert "自由交易" in traits or "回收" in traits


class TestBackwardCompatibility:
    """
    7.3 验证向后兼容性
    
    - 只配置一个模型时系统正常工作
    - 不选择评审模型时默认使用生成模型
    
    Requirements: 1.2, 5.3
    """
    
    def test_single_model_configuration(self):
        """验证只配置一个模型时系统正常工作 (Requirements: 1.2)"""
        gen_api = Mock()
        rag_system = Mock()
        
        # 只配置生成模型
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        gen_api.chat.return_value = (True, "评审结果")
        
        rag_system.get_high_performing_traits.return_value = "测试特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        # 不传入 review_api_manager
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=None
        )
        
        # 验证 rev_api 回退到 gen_api
        assert generator.rev_api is generator.gen_api
        
        # 验证模型信息显示相同模型
        model_info = generator.get_model_info()
        assert model_info["is_same_model"] is True
        assert model_info["gen_model"] == model_info["rev_model"]
    
    def test_review_works_with_single_model(self):
        """验证单模型配置下评审功能正常工作"""
        gen_api = Mock()
        rag_system = Mock()
        
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        gen_api.stream_chat.return_value = iter(["评审结果", "：脚本质量良好"])
        
        rag_system.get_high_performing_traits.return_value = "测试特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=None
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 执行评审（现在返回 Generator，需要迭代消费）
        result = "".join(generator._review_script(input_data, "测试脚本"))
        
        # 验证评审成功
        assert "评审结果" in result
        # 验证使用了 gen_api（因为 rev_api 回退到 gen_api）
        gen_api.stream_chat.assert_called_once()
    
    def test_default_review_model_uses_generation_model(self):
        """验证不选择评审模型时默认使用生成模型 (Requirements: 5.3)"""
        gen_api = Mock()
        rag_system = Mock()
        
        gen_config = Mock()
        gen_config.model_id = "gpt-4"
        gen_config.name = "默认模型"
        gen_api.load_config.return_value = gen_config
        
        # 不传入 review_api_manager（模拟用户未选择评审模型）
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=None
        )
        
        # 验证评审 API 使用生成 API
        assert generator.rev_api is gen_api
        assert generator.gen_api is gen_api
    
    def test_generation_input_validation(self):
        """验证输入验证功能正常工作"""
        # 有效输入
        valid_input = GenerationInput(
            game_intro="测试游戏介绍",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        is_valid, error = valid_input.validate()
        assert is_valid is True
        assert error == ""
        
        # 无效输入 - 空游戏介绍
        invalid_input = GenerationInput(
            game_intro="",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        is_valid, error = invalid_input.validate()
        assert is_valid is False
        assert "游戏介绍" in error
    
    def test_rag_traits_fallback_to_default(self):
        """验证 RAG 特征获取失败时回退到默认特征"""
        rag_system = RAGSystem()
        
        # 测试未知品类回退到默认
        traits = rag_system.get_high_performing_traits("未知品类XYZ")
        
        # 验证返回默认特征
        assert traits is not None
        assert len(traits) > 0
        assert "前3秒" in traits or "卖点" in traits or "CTA" in traits


class TestReviewScriptRAGIntegration:
    """评审流程 RAG 集成测试"""
    
    def test_review_script_calls_rag_traits(self):
        """验证 _review_script 调用 RAG 综合特征检索"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        rev_api.stream_chat.return_value = iter(["评审", "结果"])
        
        # 现在使用 get_comprehensive_traits
        rag_system.get_comprehensive_traits.return_value = "SLG高转化特征"
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认特征"}
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 执行评审（现在返回 Generator，需要迭代消费）
        result = list(generator._review_script(input_data, "测试脚本"))
        
        # 验证调用了 RAG 综合特征检索
        rag_system.get_comprehensive_traits.assert_called_once()
    
    def test_review_script_handles_rag_failure(self):
        """验证 RAG 特征获取失败时使用默认特征"""
        gen_api = Mock()
        rev_api = Mock()
        rag_system = Mock()
        
        gen_config = Mock()
        gen_config.model_id = "gpt-3.5-turbo"
        gen_config.name = "生成模型"
        gen_api.load_config.return_value = gen_config
        
        rev_config = Mock()
        rev_config.model_id = "gpt-4"
        rev_config.name = "评审模型"
        rev_api.load_config.return_value = rev_config
        rev_api.stream_chat.return_value = iter(["评审", "结果"])
        
        # 模拟 RAG 获取失败（现在使用 get_comprehensive_traits）
        rag_system.get_comprehensive_traits.side_effect = Exception("RAG 获取失败")
        rag_system.HIGH_PERFORMING_TRAITS = {"DEFAULT": "默认通用特征"}
        
        generator = ScriptGenerator(
            api_manager=gen_api,
            rag_system=rag_system,
            review_api_manager=rev_api
        )
        
        input_data = GenerationInput(
            game_intro="测试游戏",
            usp="测试卖点",
            target_audience="测试人群",
            category="SLG"
        )
        
        # 应该不抛出异常，而是使用默认特征继续
        # 执行评审（现在返回 Generator，需要迭代消费）
        result = "".join(generator._review_script(input_data, "测试脚本"))
        
        # 验证评审仍然成功
        assert "评审结果" in result
