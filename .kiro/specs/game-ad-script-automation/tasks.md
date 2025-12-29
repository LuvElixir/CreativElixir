# Implementation Plan: 游戏信息流广告脚本自动化工具

## Overview

采用自底向上的实现策略，先构建基础存储和配置模块，再实现 RAG 和项目管理，最后完成脚本生成工作流和 UI 界面。使用 Python 3.10+、Streamlit、LangChain 和 ChromaDB 技术栈。

## Tasks

- [x] 1. 项目初始化和基础结构
  - [x] 1.1 创建项目目录结构和依赖配置
    - 创建 `src/`、`tests/`、`data/` 目录
    - 创建 `requirements.txt` 包含 streamlit, langchain, chromadb, openai, hypothesis, pytest
    - 创建 `.streamlit/config.toml` 配置深色主题
    - _Requirements: 5.1, 6.1-6.4_

- [-] 2. API 配置管理模块
  - [x] 2.1 实现 APIConfig 数据类和 APIManager 核心逻辑
    - 创建 `src/api_manager.py`
    - 实现配置保存到 `./data/config.json`
    - 实现配置加载和动态切换
    - 实现 OpenAI 兼容客户端创建
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6_
  - [ ]* 2.2 编写 API 配置 Round-Trip 属性测试
    - **Property 1: API 配置 Round-Trip**
    - **Validates: Requirements 1.2, 1.6**
  - [ ]* 2.3 编写无效配置错误处理属性测试
    - **Property 2: 无效 API 配置错误处理**
    - **Validates: Requirements 1.5**

- [x] 3. RAG 知识库系统
  - [x] 3.1 实现 RAGSystem 核心逻辑
    - 创建 `src/rag_system.py`
    - 使用 ChromaDB 作为向量存储
    - 实现按品类分类的脚本添加和检索
    - 数据存储在 `./data/vector_db` 和 `./data/scripts`
    - _Requirements: 2.1, 2.2, 2.6_
  - [x] 3.2 实现知识库导入导出功能
    - 实现 `export_knowledge_base()` 打包为 zip
    - 实现 `import_knowledge_base()` 解压并重载
    - _Requirements: 2.3, 2.4_
  - [ ]* 3.3 编写知识库 Round-Trip 属性测试
    - **Property 3: 知识库 Round-Trip**
    - **Validates: Requirements 2.3, 2.4**
  - [ ]* 3.4 编写脚本品类分类存储属性测试
    - **Property 4: 脚本品类分类存储**
    - **Validates: Requirements 2.2, 2.5**

- [x] 4. 项目归档管理模块
  - [x] 4.1 实现 Project 和 ScriptRecord 数据类
    - 创建 `src/project_manager.py`
    - 定义项目和脚本记录的数据结构
    - _Requirements: 3.1, 3.2_
  - [x] 4.2 实现 ProjectManager 核心逻辑
    - 实现项目创建、加载、更新、删除
    - 实现脚本历史记录管理
    - 数据存储在 `./data/projects/{client}/{project}/`
    - _Requirements: 3.3, 3.4, 3.5_
  - [ ]* 4.3 编写项目数据 Round-Trip 属性测试
    - **Property 5: 项目数据 Round-Trip**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 5. Checkpoint - 基础模块验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 6. 脚本生成工作流
  - [x] 6.1 实现 GenerationInput 和 ScriptOutput 数据类
    - 创建 `src/script_generator.py`
    - 定义输入验证逻辑
    - 定义三栏输出解析逻辑
    - _Requirements: 4.1, 4.6_
  - [x] 6.2 实现 ScriptGenerator 生成工作流
    - 实现 RAG 检索 -> 生成初稿 -> 评审 -> 迭代修正流程
    - 支持流式输出
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.7_
  - [ ]* 6.3 编写脚本输出解析属性测试
    - **Property 6: 脚本输出解析**
    - **Validates: Requirements 4.6**
  - [ ]* 6.4 编写输入验证属性测试
    - **Property 7: 输入验证**
    - **Validates: Requirements 4.1**

- [x] 7. Streamlit UI 界面
  - [x] 7.1 创建主应用框架和侧边栏
    - 创建 `app.py`
    - 实现深色主题配置
    - 实现侧边栏：API 设置、项目管理、知识库管理
    - _Requirements: 5.1, 5.2, 5.6_
  - [x] 7.2 实现脚本生成主界面
    - 实现输入表单：游戏介绍、USP、目标人群、品类选择
    - 实现流式输出展示
    - 实现三栏表格结果展示
    - 实现"入库"按钮
    - _Requirements: 5.3, 5.4, 5.5, 2.5_
  - [x] 7.3 实现知识库管理界面
    - 实现品类筛选和脚本列表
    - 实现导入/导出按钮
    - _Requirements: 2.3, 2.4, 5.6_
  - [x] 7.4 实现项目历史界面
    - 实现项目选择和历史脚本列表
    - _Requirements: 3.3_

- [x] 8. 集成和优化
  - [x] 8.1 整合所有模块并完善错误处理
    - 确保各模块正确协作
    - 添加用户友好的错误提示
    - _Requirements: 1.5_
  - [x] 8.2 创建 Prompt 模板
    - 创建 `src/prompts.py`
    - 定义脚本生成、评审、修正的 Prompt 模板
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 9. Final Checkpoint - 完整功能验证
  - 确保所有测试通过，如有问题请询问用户

## Notes

- 标记 `*` 的任务为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试使用 Hypothesis 库，每个属性至少运行 100 次迭代
