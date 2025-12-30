# Requirements Document

## Introduction

本功能旨在改造脚本生成流程中的评审阶段，将原本阻塞式的评审调用改为流式输出，并在前端实现一个"辩论直播"界面，让用户能够实时看到 AI 评审委员会的思维链过程，提升用户体验和等待过程的趣味性。

## Glossary

- **Script_Generator**: 脚本生成器模块，负责广告脚本的生成工作流
- **Review_API**: 评审专用 API 管理器，用于调用 LLM 进行脚本评审
- **Stream_Chat**: 流式聊天接口，逐块返回 LLM 响应内容
- **Debate_Container**: 辩论容器，前端用于展示评审思维链的 UI 组件
- **Thought_Chain**: 思维链，AI 评审过程中的推理步骤和角色辩论内容
- **Generation_Step**: 生成步骤状态对象，用于追踪工作流各阶段

## Requirements

### Requirement 1: 流式评审后端支持

**User Story:** As a developer, I want the review process to support streaming output, so that the frontend can display the review content in real-time.

#### Acceptance Criteria

1. WHEN the `_review_script` method is called, THE Script_Generator SHALL yield text chunks instead of returning a complete string
2. WHEN streaming review content, THE Script_Generator SHALL use `self.rev_api.stream_chat()` instead of `self.rev_api.chat()`
3. WHEN the review streaming completes, THE Script_Generator SHALL have accumulated the complete review feedback for subsequent refine step
4. IF the streaming encounters an error, THEN THE Script_Generator SHALL yield an error message and handle gracefully

### Requirement 2: 生成流程适配流式评审

**User Story:** As a developer, I want the generate method to properly handle the streaming review, so that the workflow remains functional while supporting real-time output.

#### Acceptance Criteria

1. WHEN the generate method enters the review step, THE Script_Generator SHALL iterate through the `_review_script` generator and yield each chunk
2. WHILE iterating through review chunks, THE Script_Generator SHALL accumulate content into `review_feedback` variable
3. WHEN review streaming completes, THE Script_Generator SHALL pass the complete `review_feedback` to the refine step
4. WHEN yielding review chunks, THE Script_Generator SHALL prefix with a marker to identify review phase content

### Requirement 3: 辩论容器 UI 组件

**User Story:** As a user, I want to see a dedicated debate container during the review phase, so that I can watch the AI review process unfold in real-time.

#### Acceptance Criteria

1. WHEN the generation enters the review phase, THE Frontend SHALL create an expander with title "⚔️ 评审委员会激烈辩论中 (思维链)..."
2. THE Debate_Container SHALL remain expanded (expanded=True) during the review phase
3. WHEN review content is received, THE Frontend SHALL render it as markdown inside the expander
4. WHEN the review phase completes, THE Debate_Container SHALL remain visible with the complete content

### Requirement 4: 实时内容渲染

**User Story:** As a user, I want to see the review content update in real-time, so that I can follow the AI's thought process as it happens.

#### Acceptance Criteria

1. WHEN a review chunk is received, THE Frontend SHALL append it to the accumulated content
2. WHEN content is updated, THE Frontend SHALL re-render the markdown in the empty container
3. THE Frontend SHALL use `st.empty()` container for efficient real-time updates
4. WHEN rendering markdown, THE Frontend SHALL preserve formatting including headers and lists

### Requirement 5: 辩论模式 CSS 样式

**User Story:** As a user, I want the debate content to have a visually appealing style, so that the review process feels like watching a real debate.

#### Acceptance Criteria

1. THE CSS SHALL style h3 headers (角色标题) with a dark background (#374151)
2. THE CSS SHALL add a left border accent (4px solid #6366f1) to role headers
3. THE CSS SHALL apply padding (10px 15px) and border-radius (8px) to role headers
4. THE CSS SHALL set appropriate font-size (16px) and margin-top (20px) for role headers
5. THE CSS SHALL use flexbox (display: flex, align-items: center) for header layout

