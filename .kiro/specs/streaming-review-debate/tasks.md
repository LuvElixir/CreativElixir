# Implementation Plan: Streaming Review Debate

## Overview

本实现计划将脚本生成流程中的评审阶段改造为流式输出，并在前端实现"辩论直播"界面。实现分为三个主要部分：后端流式支持、前端 UI 改造、CSS 样式增强。

## Tasks

- [x] 1. 后端流式评审支持
  - [x] 1.1 修改 `_review_script` 方法为 Generator
    - 将返回类型从 `str` 改为 `Generator[str, None, None]`
    - 使用 `self.rev_api.stream_chat()` 替代 `self.rev_api.chat()`
    - 保留 RAG 特征获取和 Prompt 构建逻辑
    - _Requirements: 1.1, 1.2_

  - [x] 1.2 修改 `generate` 方法的评审部分
    - 迭代 `_review_script` Generator 并 yield 每个 chunk
    - 为评审 chunks 添加 `[REVIEW]` 前缀标记
    - 累积 `review_feedback` 变量用于后续 refine 步骤
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 1.3 编写后端单元测试
    - 测试 `_review_script` 返回 Generator 类型
    - 测试 `stream_chat` 被调用而非 `chat`
    - 测试错误处理 yield 错误消息
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. 前端辩论 UI 实现
  - [x] 2.1 修改 `render_script_generation_page` 生成循环
    - 检测 `[REVIEW]` 标记识别评审阶段
    - 创建 `st.expander` 辩论容器 (expanded=True)
    - 使用 `st.empty()` 实现实时内容更新
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_

  - [ ]* 2.2 编写前端集成测试
    - 测试辩论容器创建和状态
    - 测试内容累积和渲染
    - _Requirements: 3.1, 3.2, 4.1, 4.4_

- [x] 3. CSS 样式增强
  - [x] 3.1 在 `inject_custom_css` 添加辩论模式样式
    - 添加 `.debate-container h3` 样式规则
    - 设置 background-color, border-left, padding, border-radius
    - 设置 font-size, margin-top, display, align-items
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 3.2 编写 CSS 属性测试
    - **Property 5: CSS Debate Style Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 4. Checkpoint - 功能验证
  - 确保所有测试通过
  - 手动验证流式评审和辩论 UI 效果
  - 如有问题请向用户确认

- [ ]* 5. 属性测试实现
  - [ ]* 5.1 编写 Property 2 测试 (Content Accumulation)
    - **Property 2: Content Accumulation Correctness**
    - **Validates: Requirements 1.3, 2.2, 2.3**

  - [ ]* 5.2 编写 Property 3 测试 (Chunk Marker Consistency)
    - **Property 3: Chunk Marker Consistency**
    - **Validates: Requirements 2.4**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 后端改动集中在 `src/script_generator.py`
- 前端改动集中在 `app.py` 的 `render_script_generation_page` 和 `inject_custom_css`
- 评审 chunks 使用 `[REVIEW]` 前缀标记，前端需要 strip 后再显示

