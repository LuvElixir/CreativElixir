# Requirements Document

## Introduction

本需求文档定义了知识库系统从"文件管理"向"智能资产管理"转型的功能需求。核心目标是实现"纯文本粘贴 -> AI 自动打标 -> 结构化入库"的完整工作流，降低用户存储灵感的阻力，提升知识库的智能化程度。

## Glossary

- **RAG_System**: 检索增强生成系统，负责脚本的存储、检索和向量化处理
- **EnhancedScriptMetadata**: 增强型脚本元数据结构，包含丰富的标签体系以支持精准检索
- **Auto_Tagging_Engine**: AI 自动打标引擎，负责将非结构化文案转化为结构化元数据
- **Quick_Capture_Panel**: 快速采集面板，提供纯文本粘贴入口和 AI 分析功能
- **API_Manager**: API 管理器，负责调用 LLM 进行文本分析
- **Category**: 游戏核心品类，如 SLG、MMO、卡牌、休闲、二次元、模拟经营、射击、其他
- **Gameplay_Tags**: 玩法标签列表，描述文案中涉及的具体玩法（如抽卡、攻城、合成、捏脸）
- **Hook_Type**: 开头钩子类型，描述脚本前3秒的吸睛手段（如福利诱惑、巨大反差、失败展示）
- **Visual_Style**: 视觉暗示风格，描述脚本暗示的画面风格
- **JSON_Mode**: LLM 的 JSON 输出模式，确保返回格式化的 JSON 数据

## Requirements

### Requirement 1: Enhanced Metadata Structure

**User Story:** As a knowledge base administrator, I want to store richer metadata for each script, so that I can perform more precise retrieval and analysis.

#### Acceptance Criteria

1. THE RAG_System SHALL support EnhancedScriptMetadata with the following fields: game_name, category, gameplay_tags, hook_type, visual_style, summary, source, archived_at
2. WHEN loading legacy script files that lack new metadata fields, THE RAG_System SHALL provide default values for missing fields
3. THE EnhancedScriptMetadata SHALL maintain backward compatibility with existing ScriptMetadata by preserving game_name, source, and archived_at fields
4. WHEN serializing EnhancedScriptMetadata to JSON, THE RAG_System SHALL produce valid JSON output
5. WHEN deserializing JSON to EnhancedScriptMetadata, THE RAG_System SHALL correctly parse all fields including list-type gameplay_tags

### Requirement 2: Auto-Tagging Prompt Template

**User Story:** As a system developer, I want a well-designed prompt template for auto-tagging, so that the LLM can accurately extract structured metadata from unstructured ad copy.

#### Acceptance Criteria

1. THE Auto_Tagging_Engine SHALL use AUTO_TAGGING_TEMPLATE to instruct LLM to extract: game_name, category, gameplay_tags, hook_type, visual_style, summary
2. WHEN the raw content is provided, THE AUTO_TAGGING_TEMPLATE SHALL format the content into the prompt correctly
3. THE AUTO_TAGGING_TEMPLATE SHALL specify valid category options: SLG, MMO, 卡牌, 休闲, 二次元, 模拟经营, 射击, 其他
4. THE AUTO_TAGGING_TEMPLATE SHALL limit gameplay_tags to a maximum of 3 items
5. THE AUTO_TAGGING_TEMPLATE SHALL require JSON-only output format with example structure

### Requirement 3: Auto-Ingest Script Logic

**User Story:** As a content creator, I want to paste raw ad copy and have the system automatically analyze and store it, so that I can quickly capture creative inspiration without manual tagging.

#### Acceptance Criteria

1. WHEN raw text is provided to auto_ingest_script method, THE RAG_System SHALL call API_Manager to execute the auto-tagging prompt
2. WHEN LLM returns valid JSON, THE RAG_System SHALL parse it into EnhancedScriptMetadata
3. IF LLM returns non-JSON format, THEN THE RAG_System SHALL attempt fallback parsing or return an error with clear message
4. WHEN metadata is successfully extracted, THE RAG_System SHALL automatically determine storage path based on the category field
5. WHEN auto-ingest completes successfully, THE RAG_System SHALL write the script to both file system and vector database (if available)
6. WHEN auto-ingest completes, THE RAG_System SHALL return the extracted metadata and script ID for UI feedback

### Requirement 4: Quick Capture UI Panel

**User Story:** As a user, I want a prominent quick capture panel on the knowledge base page, so that I can easily paste and submit ad copy for AI analysis.

#### Acceptance Criteria

1. WHEN the knowledge base page loads, THE Quick_Capture_Panel SHALL be displayed at the top with an expanded expander titled "🚀 快速采集 (AI 智能打标)"
2. THE Quick_Capture_Panel SHALL contain a text area for pasting ad copy
3. THE Quick_Capture_Panel SHALL contain a primary button labeled "AI 分析并入库"
4. WHEN the button is clicked with non-empty text, THE Quick_Capture_Panel SHALL display a spinner with message "AI 正在阅读并打标签..."
5. WHEN auto-ingest succeeds, THE Quick_Capture_Panel SHALL display success message showing the archived category
6. WHEN auto-ingest succeeds, THE Quick_Capture_Panel SHALL display the extracted metadata as JSON for user verification
7. IF auto-ingest fails, THEN THE Quick_Capture_Panel SHALL display an error message with details

### Requirement 5: Legacy Import Deprecation

**User Story:** As a product designer, I want to de-emphasize the legacy ZIP import feature, so that users are guided toward the new quick capture workflow.

#### Acceptance Criteria

1. THE knowledge base page SHALL move the ZIP upload functionality to a collapsed section at the bottom
2. THE ZIP upload section SHALL be labeled as "📦 批量导入工具 (高级)"
3. THE Quick_Capture_Panel SHALL be positioned above all other content on the knowledge base page
4. WHEN the page loads, THE Quick_Capture_Panel expander SHALL be expanded by default while the ZIP import section SHALL be collapsed

### Requirement 6: Error Handling and Retry

**User Story:** As a system operator, I want robust error handling for LLM responses, so that the system gracefully handles malformed outputs.

#### Acceptance Criteria

1. IF LLM response is empty or null, THEN THE Auto_Tagging_Engine SHALL return an error indicating "AI 返回为空"
2. IF LLM response cannot be parsed as JSON, THEN THE Auto_Tagging_Engine SHALL attempt to extract JSON from markdown code blocks
3. IF JSON extraction fails after fallback attempts, THEN THE Auto_Tagging_Engine SHALL return an error with the raw response for debugging
4. WHEN JSON parsing succeeds but required fields are missing, THE Auto_Tagging_Engine SHALL use default values: game_name="未知", category="其他", gameplay_tags=[], hook_type="", visual_style="", summary=""
