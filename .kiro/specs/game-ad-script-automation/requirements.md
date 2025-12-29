# Requirements Document

## Introduction

游戏信息流广告脚本自动化工具是一个内部使用的 AI 驱动应用，旨在帮助广告创意团队快速生成高质量的游戏广告脚本。该工具整合了灵活的 LLM API 管理、可插拔的 RAG 知识库系统、以及完整的项目工作流管理，通过检索同品类爆款脚本并结合 AI 生成与评审迭代，输出标准化的三栏广告脚本表格（分镜、口播、设计意图）。

## Glossary

- **Script_Generator**: 核心脚本生成系统，负责调用 LLM 生成广告脚本初稿
- **Review_Model**: 评审模型，负责评估生成的脚本并给出修改意见
- **RAG_System**: 检索增强生成系统，基于 ChromaDB 存储和检索同品类爆款脚本
- **Knowledge_Base**: 向量知识库，按游戏品类分类存储脚本数据
- **Project_Manager**: 项目管理模块，以客户/项目维度归档数据
- **API_Manager**: API 配置管理模块，支持多种 OpenAI 兼容格式的 LLM 接入
- **Config_Store**: 配置持久化存储，保存 API 密钥和系统设置
- **Script_Output**: 标准三栏表格输出格式（分镜、口播、设计意图）
- **Game_Category**: 游戏品类分类（如 SLG、MMO、休闲等）
- **USP**: Unique Selling Point，游戏独特卖点

## Requirements

### Requirement 1: API 配置管理

**User Story:** As a 广告创意人员, I want 在设置页面配置和管理 LLM API, so that 我可以灵活接入不同的 AI 模型服务。

#### Acceptance Criteria

1. WHEN 用户访问设置页面 THEN THE API_Manager SHALL 显示 API Key、Base URL 和 Model ID 的输入表单
2. WHEN 用户提交 API 配置 THEN THE Config_Store SHALL 将配置保存到本地 config.json 文件
3. WHEN 用户切换模型配置 THEN THE API_Manager SHALL 动态加载新的模型配置而无需重启应用
4. WHEN 用户配置文心一言或豆包等兼容 OpenAI 格式的 API THEN THE API_Manager SHALL 正确解析并调用该 API
5. IF API 配置无效或连接失败 THEN THE API_Manager SHALL 显示明确的错误提示信息
6. WHEN 应用启动时 THEN THE Config_Store SHALL 自动加载已保存的 API 配置

### Requirement 2: RAG 知识库管理

**User Story:** As a 广告创意人员, I want 管理按游戏品类分类的脚本知识库, so that 我可以检索同品类的爆款脚本作为参考。

#### Acceptance Criteria

1. THE Knowledge_Base SHALL 使用 ChromaDB 作为本地向量存储引擎
2. WHEN 添加脚本到知识库 THEN THE RAG_System SHALL 按游戏品类（SLG、MMO、休闲等）分类存储
3. WHEN 用户点击"导出知识库" THEN THE Knowledge_Base SHALL 将向量库目录和原始数据打包为 .zip 文件
4. WHEN 用户上传 .zip 数据包 THEN THE Knowledge_Base SHALL 解压并自动重新加载知识库
5. WHEN 用户点击"入库"按钮 THEN THE RAG_System SHALL 将当前生成的脚本存入对应品类的知识库
6. THE Knowledge_Base SHALL 将所有数据存储在项目的 ./data 目录下

### Requirement 3: 项目归档管理

**User Story:** As a 广告创意人员, I want 以客户/项目维度管理工作内容, so that 我可以独立存储和追溯每个项目的历史数据。

#### Acceptance Criteria

1. WHEN 用户创建新项目 THEN THE Project_Manager SHALL 创建独立的项目目录结构
2. THE Project_Manager SHALL 为每个项目独立存储游戏介绍、卖点和历史生成脚本
3. WHEN 用户选择项目 THEN THE Project_Manager SHALL 加载该项目的所有历史数据
4. WHEN 生成新脚本 THEN THE Project_Manager SHALL 自动保存到当前项目的历史记录中
5. THE Project_Manager SHALL 支持按客户名称和项目名称进行层级管理

### Requirement 4: 脚本生成工作流

**User Story:** As a 广告创意人员, I want 通过自动化工作流生成高质量广告脚本, so that 我可以快速产出符合标准的创意内容。

#### Acceptance Criteria

1. WHEN 用户输入游戏介绍、USP 和目标人群 THEN THE Script_Generator SHALL 接收并验证输入数据
2. WHEN 开始生成流程 THEN THE RAG_System SHALL 首先检索同品类的爆款脚本作为参考
3. WHEN RAG 检索完成 THEN THE Script_Generator SHALL 基于检索结果和用户输入生成脚本初稿
4. WHEN 初稿生成完成 THEN THE Review_Model SHALL 评估脚本质量并给出修改意见
5. WHEN 收到修改意见 THEN THE Script_Generator SHALL 自动迭代修正脚本
6. WHEN 脚本生成完成 THEN THE Script_Output SHALL 以标准三栏表格格式输出（分镜、口播、设计意图）
7. WHILE 生成过程进行中 THEN THE Script_Generator SHALL 以流式输出方式展示生成进度

### Requirement 5: 用户界面设计

**User Story:** As a 广告创意人员, I want 使用现代化的深色主题界面, so that 我可以获得舒适高效的使用体验。

#### Acceptance Criteria

1. THE UI SHALL 采用深色模式 (Dark Theme) 作为默认主题
2. THE UI SHALL 在侧边栏提供项目管理和 API 设置功能
3. THE UI SHALL 在主界面以流式输出方式展示脚本生成过程
4. THE UI SHALL 使用 st.tabs 或 st.expander 组织输入和输出区域
5. WHEN 脚本生成完成 THEN THE UI SHALL 显示"入库"按钮供用户将脚本存入知识库
6. THE UI SHALL 提供知识库导入/导出的操作按钮

### Requirement 6: 数据持久化

**User Story:** As a 系统管理员, I want 所有数据集中存储在指定目录, so that 我可以方便地进行数据迁移和备份。

#### Acceptance Criteria

1. THE Config_Store SHALL 将 API 配置保存到 ./data/config.json
2. THE Knowledge_Base SHALL 将向量数据存储到 ./data/vector_db 目录
3. THE Project_Manager SHALL 将项目数据存储到 ./data/projects 目录
4. THE RAG_System SHALL 将原始脚本数据存储到 ./data/scripts 目录
5. WHEN 导出知识库 THEN THE Knowledge_Base SHALL 包含 ./data 目录下的所有相关数据
