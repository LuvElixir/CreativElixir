# Implementation Plan: UI/UX SaaS 风格重构

## Overview

采用自顶向下的实现策略，先更新主题配置和 CSS 注入，再重构导航结构，最后优化各页面的布局和交互。使用 Python + Streamlit + streamlit-option-menu 技术栈。

## Tasks

- [x] 1. 依赖安装和主题配置
  - [x] 1.1 更新 requirements.txt 添加 streamlit-option-menu 依赖
    - 添加 `streamlit-option-menu>=0.3.6`
    - _Requirements: 依赖变更_
  - [x] 1.2 更新 .streamlit/config.toml 主题配置
    - primaryColor: #6366f1
    - backgroundColor: #111827
    - secondaryBackgroundColor: #1f2937
    - textColor: #f9fafb
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [ ]* 1.3 编写主题配置正确性测试
    - **Property 1: 主题配置正确性**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [x] 2. CSS 注入模块实现
  - [x] 2.1 在 app.py 中实现 inject_custom_css() 函数
    - 隐藏 #MainMenu 和 footer
    - 定义卡片容器样式 (.st-card)
    - 定义输入组件圆角样式
    - 定义按钮样式优化
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [ ]* 2.2 编写 CSS 样式定义正确性测试
    - **Property 4: CSS 样式定义正确性**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 3. 侧边栏导航重构
  - [x] 3.1 实现 render_navigation() 函数
    - 使用 streamlit-option-menu 创建导航菜单
    - 配置菜单项：脚本生成、知识库、项目历史、设置
    - 配置图标：pen-tool、database、clock-history、gear
    - 配置深色主题样式
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [ ]* 3.2 编写导航菜单配置正确性测试
    - **Property 3: 导航菜单配置正确性**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.6**

- [x] 4. Emoji 清理
  - [x] 4.1 移除所有标题、按钮、提示信息中的 Emoji
    - 清理 st.markdown 标题中的 Emoji
    - 清理 st.button 文本中的 Emoji
    - 清理 st.info/warning/error/success 中的 Emoji
    - 清理 st.expander 标题中的 Emoji
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]* 4.2 编写 Emoji 清理完整性测试
    - **Property 2: Emoji 清理完整性**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [x] 5. Checkpoint - 基础重构验证
  - 确保应用可正常启动，导航菜单工作正常

- [x] 6. 脚本生成页优化
  - [x] 6.1 重构输入区域为多列紧凑布局
    - 使用 st.columns 组织输入框
    - 项目名称、品类选择放在同一行
    - 游戏介绍、卖点、目标人群合理分布
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 6.2 实现 st.status 包裹生成过程
    - 使用 st.status("正在构建创意...", expanded=True)
    - 在 status 容器内显示 RAG 检索、生成、评审、修正日志
    - 完成后调用 status.update(expanded=False, state="complete")
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ]* 6.3 编写状态容器配置正确性测试
    - **Property 5: 状态容器配置正确性**
    - **Validates: Requirements 6.2, 6.3, 6.4**
  - [x] 6.4 实现 st.data_editor 结果展示
    - 替代原有 Markdown 表格
    - 配置分镜、口播、设计意图三列
    - 入库按钮放在表格下方右侧，use_container_width=False
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [ ]* 6.5 编写结果展示配置正确性测试
    - **Property 6: 结果展示配置正确性**
    - **Validates: Requirements 7.2, 7.5**

- [x] 7. 设置页面整合
  - [x] 7.1 创建独立的设置页面渲染函数
    - 将原侧边栏的 API 设置功能移至设置页面
    - 将原侧边栏的提示词管理功能移至设置页面
    - 使用 st.tabs 组织 API 配置和提示词管理
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 8. 知识库页和项目历史页优化
  - [x] 8.1 优化知识库页面布局
    - 移除 Emoji，保持纯文字
    - 优化脚本列表展示
    - _Requirements: 3.1, 3.2, 3.3_
  - [x] 8.2 优化项目历史页面布局
    - 移除 Emoji，保持纯文字
    - 优化历史脚本展示
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 9. 主程序入口重构
  - [x] 9.1 重构 main() 函数
    - 调用 inject_custom_css()
    - 调用 render_navigation() 获取选中页面
    - 根据选中页面渲染对应内容
    - 移除原有的 render_sidebar() 调用
    - _Requirements: 4.5_

- [x] 10. Final Checkpoint - 完整功能验证
  - 确保所有页面正常工作
  - 确保原有业务逻辑不受影响
  - 如有问题请询问用户

## Notes

- 标记 `*` 的任务为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 核心业务逻辑（RAGSystem、ScriptGenerator 等）保持不变，仅修改 UI 渲染层代码
- 新增依赖：`pip install streamlit-option-menu`

