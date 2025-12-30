# Requirements Document

## Introduction

本需求文档描述了 CreativElixir 项目的评审模块重构方案。当前系统的广告脚本评审功能存在局限性：生成和评审使用同一个模型（导致思维同质化），且评审缺乏真实市场数据支撑（空对空评审）。本次重构将实现"双模型架构"（生成与评审分离）+ "多角色委员会"（引入投放、玩家、产品视角）+ "RAG 真实数据标准"（基于高转化特征评审）。

## Glossary

- **Script_Generator**: 核心脚本生成系统，负责调用 LLM 生成广告脚本初稿
- **Gen_API_Manager**: 生成专用 API 管理器，用于脚本初稿生成
- **Rev_API_Manager**: 评审专用 API 管理器，用于脚本评审（可与生成使用不同模型）
- **Review_Committee**: 评审委员会，由三个虚拟角色组成的多视角评审系统
- **UA_Specialist**: 资深投放投手角色，关注黄金前3秒、无效镜头、CTA 诱惑力
- **Hardcore_Gamer**: 硬核游戏玩家角色，关注真实性、术语准确性、爽点还原度
- **Product_Manager**: 产品经理角色，关注 USP 传达清晰度、人群匹配度
- **RAG_Traits**: 从知识库检索的高转化广告特征标准
- **High_Performing_Traits**: 同品类高转化广告的共性特征
- **Advanced_Review_Template**: 高级评审 Prompt 模板，包含多角色评审和 RAG 标准

## Requirements

### Requirement 1: 双模型架构支持

**User Story:** As a 广告创意人员, I want 使用不同的模型进行脚本生成和评审, so that 我可以获得更多元化的创意视角，避免思维同质化。

#### Acceptance Criteria

1. WHEN 初始化 ScriptGenerator THEN THE Script_Generator SHALL 支持传入两个独立的 API 管理器：gen_api_manager（生成用）和 review_api_manager（评审用）
2. IF review_api_manager 未提供 THEN THE Script_Generator SHALL 默认使用 gen_api_manager 进行评审（保持向后兼容）
3. WHEN 执行脚本生成流程 THEN THE Script_Generator SHALL 使用 gen_api_manager 调用生成模型
4. WHEN 执行脚本评审流程 THEN THE Script_Generator SHALL 使用 rev_api_manager 调用评审模型
5. THE Script_Generator SHALL 在日志中记录当前使用的生成模型和评审模型名称

### Requirement 2: RAG 高转化特征检索

**User Story:** As a 广告创意人员, I want 评审时参考同品类高转化广告的特征标准, so that 评审意见有真实市场数据支撑，而非空对空评审。

#### Acceptance Criteria

1. THE RAG_System SHALL 提供 get_high_performing_traits(category: str) 方法，返回指定品类的高转化广告特征
2. WHEN category 为 "SLG" THEN THE RAG_System SHALL 返回 SLG 品类的高转化特征（前3秒战力数值跳动、以弱胜强策略反转、开局送连抽等）
3. WHEN category 为 "MMO" THEN THE RAG_System SHALL 返回 MMO 品类的高转化特征（高精度捏脸、装备发光特效、自由交易、回收利益点等）
4. WHEN category 为其他品类 THEN THE RAG_System SHALL 返回通用高转化特征（黄金前3秒吸睛、卖点清晰、强力 CTA 引导转化）
5. THE RAG_System SHALL 支持未来扩展为从向量库动态检索高转化特征

### Requirement 3: 高级评审 Prompt 模板

**User Story:** As a 广告创意人员, I want 评审意见包含多角色视角和市场标准参考, so that 我可以获得更全面、更专业的修改建议。

#### Acceptance Criteria

1. THE PromptManager SHALL 包含 ADVANCED_REVIEW_TEMPLATE 常量，定义多角色委员会评审模板
2. THE ADVANCED_REVIEW_TEMPLATE SHALL 包含三个评审角色：资深投放投手、硬核游戏玩家、产品经理
3. THE ADVANCED_REVIEW_TEMPLATE SHALL 包含 {rag_traits} 占位符，用于注入高转化特征标准
4. WHEN 调用 get_review_prompt THEN THE PromptManager SHALL 支持传入 rag_traits 参数
5. THE ADVANCED_REVIEW_TEMPLATE SHALL 要求输出主席总结和3条最高优先级修改建议
6. THE PromptManager SHALL 在 DEFAULT_PROMPTS 中注册 advanced_review 模板

### Requirement 4: 高级评审流程执行

**User Story:** As a 广告创意人员, I want 评审流程自动获取 RAG 标准并使用高级模板, so that 每次评审都能基于真实市场数据进行。

#### Acceptance Criteria

1. WHEN 执行 _review_script 方法 THEN THE Script_Generator SHALL 首先调用 rag_system.get_high_performing_traits(category) 获取高转化特征
2. WHEN 构建评审 Prompt THEN THE Script_Generator SHALL 将 rag_traits 传入 PromptManager.get_review_prompt
3. WHEN 发送评审请求 THEN THE Script_Generator SHALL 使用 rev_api_manager（评审专用 API）而非 gen_api_manager
4. THE Script_Generator SHALL 在日志中记录已获取的 RAG 高转化特征
5. IF RAG 特征获取失败 THEN THE Script_Generator SHALL 使用默认通用特征继续评审

### Requirement 5: UI 评审模型选择

**User Story:** As a 广告创意人员, I want 在界面上分别指定生成模型和评审模型, so that 我可以灵活配置不同的模型组合。

#### Acceptance Criteria

1. THE UI SHALL 在侧边栏 API 设置区域显示"评审模型"下拉选择框
2. THE UI SHALL 允许用户从已配置的 API 列表中选择评审专用模型
3. WHEN 用户未选择评审模型 THEN THE UI SHALL 默认使用当前生成模型进行评审
4. WHEN 初始化 ScriptGenerator THEN THE UI SHALL 将选中的评审模型配置传递给 review_api_manager 参数
5. THE UI SHALL 在脚本生成区域显示当前使用的生成模型和评审模型名称
6. WHEN 用户切换评审模型 THEN THE UI SHALL 立即更新 ScriptGenerator 的配置

### Requirement 6: 评审结果格式

**User Story:** As a 广告创意人员, I want 评审结果清晰展示各角色视角和修改建议, so that 我可以快速理解问题并进行修改。

#### Acceptance Criteria

1. THE Review_Committee SHALL 输出包含三个角色的分角评审意见
2. EACH 角色评审 SHALL 包含关注点和具体判词
3. THE Review_Committee SHALL 输出主席总结，包含3条最高优先级修改建议
4. EACH 修改建议 SHALL 包含问题位置、问题诊断和具体修改方案
5. THE 修改方案 SHALL 给出具体的修改后文案或画面描述

