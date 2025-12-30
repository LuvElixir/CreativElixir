# Implementation Plan: Smart Asset Management

## Overview

本实现计划将知识库系统从"文件管理"转型为"智能资产管理"。实现顺序遵循数据层 -> 逻辑层 -> 表现层的依赖关系，确保每个步骤都可以独立验证。

## Tasks

- [-] 1. 数据层：实现 EnhancedScriptMetadata
  - [x] 1.1 在 `src/rag_system.py` 中添加 EnhancedScriptMetadata 数据类
    - 定义所有字段：game_name, category, gameplay_tags, hook_type, visual_style, summary, source, archived_at
    - 实现 `from_legacy` 类方法用于从 ScriptMetadata 转换
    - 实现 `to_dict` 和 `from_dict` 方法用于序列化
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ]* 1.2 编写 EnhancedScriptMetadata 属性测试
    - **Property 1: EnhancedScriptMetadata Serialization Round-Trip**
    - **Property 2: Backward Compatibility from Legacy Format**
    - **Validates: Requirements 1.4, 1.5, 1.2, 1.3**

- [x] 2. 逻辑层：实现 AUTO_TAGGING_TEMPLATE
  - [x] 2.1 在 `src/prompts.py` 中添加 AUTO_TAGGING_TEMPLATE
    - 包含所有必需字段的提取指令
    - 指定有效的 category 选项
    - 限制 gameplay_tags 最多 3 个
    - 提供 JSON 输出示例
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [ ]* 2.2 编写模板格式化属性测试
    - **Property 3: Template Formatting Preserves Content**
    - **Validates: Requirements 2.2**

- [x] 3. 逻辑层：实现 JSON 解析与错误处理
  - [x] 3.1 在 `src/rag_system.py` 中添加 `extract_json_from_response` 函数
    - 实现直接 JSON 解析
    - 实现从 markdown 代码块提取 JSON 的 fallback
    - 返回解析结果或 None
    - _Requirements: 6.2, 6.3_
  - [x] 3.2 在 `src/rag_system.py` 中添加 `parse_auto_tag_response` 函数
    - 调用 `extract_json_from_response`
    - 应用默认值处理缺失字段
    - 返回 EnhancedScriptMetadata 或错误信息
    - _Requirements: 3.2, 6.1, 6.4_
  - [ ]* 3.3 编写 JSON 解析属性测试
    - **Property 4: JSON Parsing with Default Values**
    - **Property 5: Fallback JSON Extraction from Code Blocks**
    - **Property 6: Error Handling Returns Raw Response**
    - **Validates: Requirements 3.2, 6.2, 6.3, 6.4**

- [x] 4. Checkpoint - 确保所有测试通过
  - 运行现有测试确保无回归
  - 如有问题请询问用户

- [x] 5. 逻辑层：实现 auto_ingest_script 方法
  - [x] 5.1 在 `src/rag_system.py` 的 RAGSystem 类中添加 `auto_ingest_script` 方法
    - 接收 raw_text 参数
    - 格式化 AUTO_TAGGING_TEMPLATE
    - 调用 API_Manager 执行 LLM 请求
    - 解析响应并创建 EnhancedScriptMetadata
    - 根据 category 确定存储路径
    - 写入文件系统和向量数据库
    - 返回 (success, message, metadata) 元组
    - _Requirements: 3.1, 3.4, 3.5, 3.6_
  - [ ]* 5.2 编写 auto_ingest_script 属性测试
    - **Property 7: Category Determines Storage Path**
    - **Property 8: Successful Ingest Writes to File System**
    - **Property 9: Successful Ingest Returns Metadata and ID**
    - **Validates: Requirements 3.4, 3.5, 3.6**

- [x] 6. 表现层：实现快速采集 UI
  - [x] 6.1 在 `app.py` 中添加 `render_quick_capture_panel` 函数
    - 创建 expander 容器，标题为 "🚀 快速采集 (AI 智能打标)"
    - 添加 text_area 用于粘贴文案
    - 添加 "AI 分析并入库" 按钮
    - 实现点击后的 spinner 和结果展示
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - [x] 6.2 修改 `render_knowledge_base_tab` 函数
    - 在页面顶部调用 `render_quick_capture_panel`
    - 将 ZIP 上传功能移至底部
    - 将 ZIP 上传区域改为折叠状态，标题为 "📦 批量导入工具 (高级)"
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Final Checkpoint - 确保所有测试通过
  - 运行完整测试套件
  - 验证 UI 功能正常
  - 如有问题请询问用户

## Notes

- 任务标记 `*` 为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号以便追溯
- Checkpoint 任务用于确保增量验证
- 属性测试使用 hypothesis 库，每个属性至少运行 100 次迭代
