# Requirements Document

## Introduction

本需求文档描述了游戏广告脚本生成工具的 UI/UX 重构升级项目。目标是将当前"玩具 Demo"风格的界面升级为专业的 SaaS 工具风格，采用深色科技感主题，移除过多的 Emoji，优化布局紧凑度，并引入现代化的导航和交互模式。

## Glossary

- **UI_Theme**: Streamlit 主题配置，定义应用的视觉风格（颜色、背景等）
- **Option_Menu**: 基于 streamlit-option-menu 库的侧边栏导航组件
- **Card_Container**: 使用 CSS 实现的卡片化内容容器，提供视觉层次
- **Status_Container**: Streamlit 的 st.status 组件，用于包裹生成过程日志
- **Data_Editor**: Streamlit 的 st.data_editor 组件，用于可编辑表格展示
- **CSS_Injection**: 通过 st.markdown 注入自定义 CSS 样式

## Requirements

### Requirement 1: 主题配置升级

**User Story:** As a 用户, I want 使用深色科技感主题的界面, so that 我可以获得专业、舒适的视觉体验。

#### Acceptance Criteria

1. THE UI_Theme SHALL 使用科技蓝/紫 (#6366f1) 作为主色调替代原有红色
2. THE UI_Theme SHALL 使用深灰 (#111827) 作为主背景色
3. THE UI_Theme SHALL 使用稍浅深灰 (#1f2937) 作为次级背景色
4. THE UI_Theme SHALL 使用 #f9fafb 作为文本颜色
5. WHEN 应用加载时 THEN THE UI_Theme SHALL 自动应用深色模式配置

### Requirement 2: CSS 样式注入

**User Story:** As a 用户, I want 看到简洁专业的界面元素, so that 我可以专注于核心功能而不被冗余元素干扰。

#### Acceptance Criteria

1. THE CSS_Injection SHALL 隐藏 Streamlit 默认的汉堡菜单
2. THE CSS_Injection SHALL 隐藏 Streamlit 默认的 Footer
3. THE CSS_Injection SHALL 定义 Card_Container 样式（圆角 12px、边框 #374151、微弱背景色）
4. THE CSS_Injection SHALL 为输入组件（selectbox、text_input、text_area）添加 8px 圆角
5. WHEN 页面渲染时 THEN THE CSS_Injection SHALL 在页面顶部注入所有自定义样式

### Requirement 3: Emoji 清理

**User Story:** As a 用户, I want 看到纯文字或图标的界面元素, so that 界面看起来更加专业克制。

#### Acceptance Criteria

1. THE UI SHALL 移除所有标题中的 Emoji（如 🚀, 🎮, ⚙️, 📝 等）
2. THE UI SHALL 移除所有按钮文本中的 Emoji
3. THE UI SHALL 移除所有提示信息中的 Emoji
4. WHERE 需要图标时 THEN THE UI SHALL 使用 streamlit-option-menu 提供的图标系统

### Requirement 4: 侧边栏导航重构

**User Story:** As a 用户, I want 通过清晰的导航菜单切换功能页面, so that 我可以快速定位到需要的功能。

#### Acceptance Criteria

1. THE Option_Menu SHALL 替代原有的 st.sidebar 堆叠式布局
2. THE Option_Menu SHALL 包含四个菜单项：脚本生成、知识库、项目历史、设置
3. THE Option_Menu SHALL 使用 pen-tool、database、clock-history、gear 图标
4. THE Option_Menu SHALL 匹配深色主题样式（透明背景、#818cf8 图标色、#6366f1 选中背景）
5. WHEN 用户点击菜单项 THEN THE UI SHALL 渲染对应的主界面函数
6. THE Option_Menu SHALL 显示应用名称 "CreativElixir" 作为菜单标题

### Requirement 5: 脚本生成页输入区优化

**User Story:** As a 用户, I want 在紧凑的布局中输入生成参数, so that 我可以更高效地完成输入操作。

#### Acceptance Criteria

1. THE UI SHALL 使用 st.columns 将输入框排版为多列布局
2. THE UI SHALL 将项目名称、品类选择放在同一行
3. THE UI SHALL 将游戏介绍、卖点、目标人群等文本区域合理分布
4. THE UI SHALL 避免垂直罗列所有输入框

### Requirement 6: 生成过程展示优化

**User Story:** As a 用户, I want 在可折叠的状态容器中查看生成日志, so that 我可以选择性地查看详细过程而不被干扰。

#### Acceptance Criteria

1. WHEN 生成流程开始 THEN THE Status_Container SHALL 包裹所有生成日志
2. THE Status_Container SHALL 使用 "正在构建创意..." 作为状态标题
3. WHILE 生成进行中 THEN THE Status_Container SHALL 保持展开状态
4. WHEN 生成完成 THEN THE Status_Container SHALL 自动收起
5. THE UI SHALL 不直接在屏幕上 print 中间过程

### Requirement 7: 结果展示优化

**User Story:** As a 用户, I want 在可编辑表格中查看和修改生成的脚本, so that 我可以直接调整内容而无需复制粘贴。

#### Acceptance Criteria

1. THE Data_Editor SHALL 替代原有的 Markdown 表格展示
2. THE Data_Editor SHALL 包含分镜、口播、设计意图三列
3. THE Data_Editor SHALL 允许用户直接编辑单元格内容
4. THE UI SHALL 将"入库"按钮放在表格下方右侧
5. THE UI SHALL 为"入库"按钮设置 use_container_width=False

### Requirement 8: 设置页面整合

**User Story:** As a 用户, I want 在独立的设置页面管理 API 配置和提示词, so that 设置功能与核心功能分离。

#### Acceptance Criteria

1. WHEN 用户选择"设置"菜单 THEN THE UI SHALL 显示 API 配置管理界面
2. THE UI SHALL 将原侧边栏的 API 设置功能移至设置页面
3. THE UI SHALL 将原侧边栏的提示词管理功能移至设置页面
4. THE UI SHALL 保持原有的 API 配置保存、加载、测试功能

