# Implementation Plan: 双模型评审架构重构

## Overview

采用自底向上的实现策略，先改造数据层（RAG 特征检索），再改造提示词层（高级评审模板），然后改造核心逻辑层（ScriptGenerator 双模型支持），最后改造 UI 层（评审模型选择）。使用 Python 3.10+、Streamlit 技术栈。

## Tasks

- [x] 1. 数据层改造：RAG 高转化特征检索
  - [x] 1.1 在 RAGSystem 中新增 get_high_performing_traits 方法
    - 在 `src/rag_system.py` 中添加 HIGH_PERFORMING_TRAITS 常量
    - 实现 get_high_performing_traits(category: str) 方法
    - SLG 返回：前3秒战力数值跳动、以弱胜强策略反转、开局送连抽
    - MMO 返回：高精度捏脸、装备发光特效、自由交易、回收利益点
    - 其他品类返回：黄金前3秒吸睛、卖点清晰、强力 CTA 引导转化
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [ ]* 1.2 编写 RAG 特征检索属性测试
    - **Property 3: RAG 特征检索完整性**
    - **Validates: Requirements 2.1, 2.4**

- [x] 2. 提示词层改造：高级评审模板
  - [x] 2.1 在 PromptManager 中新增 ADVANCED_REVIEW_TEMPLATE
    - 在 `src/prompts.py` 中添加 ADVANCED_REVIEW_TEMPLATE 常量
    - 包含三个评审角色：投放投手、硬核玩家、产品经理
    - 包含 {rag_traits} 占位符
    - 包含主席总结和3条修改建议格式要求
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  - [x] 2.2 修改 get_review_prompt 方法支持 rag_traits 参数
    - 添加 rag_traits: Optional[str] = None 参数
    - 添加 use_advanced: bool = True 参数
    - 当 use_advanced=True 且 rag_traits 存在时使用高级模板
    - 在 DEFAULT_PROMPTS 中注册 advanced_review 模板
    - _Requirements: 3.4, 3.6_
  - [ ]* 2.3 编写 Prompt 模板属性测试
    - **Property 4: Prompt 模板 RAG 特征注入**
    - **Validates: Requirements 3.4**

- [x] 3. Checkpoint - 数据层和提示词层验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 4. 架构层改造：ScriptGenerator 双模型支持
  - [x] 4.1 修改 ScriptGenerator 初始化方法
    - 添加 review_api_manager: Optional[APIManager] = None 参数
    - 设置 self.gen_api = api_manager
    - 设置 self.rev_api = review_api_manager if review_api_manager else api_manager
    - 添加 get_model_info() 方法返回当前模型配置
    - _Requirements: 1.1, 1.2_
  - [x] 4.2 重写 _review_script 方法
    - 调用 self.rag_system.get_high_performing_traits(category) 获取特征
    - 调用 PromptManager.get_review_prompt 传入 rag_traits 参数
    - 使用 self.rev_api（评审专用 API）发送请求
    - 添加日志记录获取的 RAG 特征和使用的模型
    - 添加异常处理：RAG 获取失败时使用默认特征
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 4.3 编写双 API 管理器属性测试
    - **Property 1: 双 API 管理器正确分离**
    - **Property 2: 默认评审 API 回退**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 5. Checkpoint - 核心逻辑层验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 6. UI 层改造：评审模型选择
  - [x] 6.1 在侧边栏 API 设置区域增加评审模型选择
    - 在 `app.py` 的 render_api_settings 函数中添加评审模型下拉框
    - 选项包括"使用生成模型"和所有已配置的 API 配置名称
    - 将选中的评审模型保存到 st.session_state.review_api_manager
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 6.2 修改脚本生成界面显示模型信息
    - 在脚本生成区域显示当前生成模型和评审模型名称
    - 初始化 ScriptGenerator 时传入 review_api_manager 参数
    - _Requirements: 5.4, 5.5, 5.6_

- [x] 7. 集成测试和验收
  - [x] 7.1 验证双模型架构工作正常
    - 配置两个不同的 API（如 GPT-3.5 生成，GPT-4 评审）
    - 执行脚本生成流程
    - 验证日志显示正确的模型调用
    - _Requirements: 1.3, 1.4, 1.5_
  - [x] 7.2 验证评审结果包含多角色视角
    - 检查评审输出包含"投放投手"、"硬核玩家"、"产品经理"角色
    - 检查评审输出引用了 RAG 高转化标准
    - 检查评审输出包含主席总结和3条修改建议
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 7.3 验证向后兼容性
    - 只配置一个模型时系统正常工作
    - 不选择评审模型时默认使用生成模型
    - _Requirements: 1.2, 5.3_

- [x] 8. Final Checkpoint - 完整功能验证
  - 确保所有测试通过，如有问题请询问用户

## Notes

- 标记 `*` 的任务为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 实现顺序：数据层 → 提示词层 → 核心逻辑层 → UI 层
- 使用 Python 3.10+ 类型注解

