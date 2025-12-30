# Requirements Document

## Introduction

本需求文档描述游戏广告脚本生成工具的 UI 布局优化项目。目标是在现有深色科技感主题基础上，优化页面结构、信息层级和响应式设计，提升用户操作效率和视觉体验。

## Glossary

- **Page_Header**: 页面顶部区域，包含标题、状态信息和快捷操作
- **Input_Section**: 脚本生成页的输入区域，包含项目信息和生成参数
- **Result_Section**: 脚本生成结果展示区域
- **Sidebar_Navigation**: 侧边栏导航组件
- **Card_Component**: 卡片式容器组件，用于分组相关内容
- **Info_Hierarchy**: 信息层级，指内容的视觉重要性排序

## Requirements

### Requirement 1: 页面头部优化

**User Story:** As a 用户, I want 在页面顶部快速了解当前状态和执行常用操作, so that 我可以更高效地使用工具。

#### Acceptance Criteria

1. THE Page_Header SHALL 在脚本生成页显示当前项目名称和客户名称
2. THE Page_Header SHALL 显示当前使用的生成模型和评审模型信息
3. THE Page_Header SHALL 使用紧凑的单行布局展示状态信息
4. WHEN 未选择项目时 THEN THE Page_Header SHALL 显示"未选择项目"提示

### Requirement 2: 输入区域布局优化

**User Story:** As a 用户, I want 在更紧凑的布局中输入生成参数, so that 我可以在一屏内看到所有输入项并快速完成输入。

#### Acceptance Criteria

1. THE Input_Section SHALL 使用卡片组件包裹相关输入项
2. THE Input_Section SHALL 将项目信息（项目名称、客户名称、品类）放在第一个卡片中
3. THE Input_Section SHALL 将核心输入（游戏介绍、USP、目标人群）放在第二个卡片中
4. THE Input_Section SHALL 使用 3:1 的列比例布局游戏介绍和其他输入
5. THE Input_Section SHALL 将生成按钮放在输入区域底部居中位置
6. WHEN 输入区域高度超过视口时 THEN THE Input_Section SHALL 保持生成按钮可见

### Requirement 3: 结果展示区域优化

**User Story:** As a 用户, I want 在清晰的布局中查看和编辑生成结果, so that 我可以快速理解和修改脚本内容。

#### Acceptance Criteria

1. THE Result_Section SHALL 使用卡片组件包裹结果表格
2. THE Result_Section SHALL 在表格上方显示生成状态摘要（如"已生成 N 个分镜"）
3. THE Result_Section SHALL 将操作按钮（入库、导出）放在表格下方右侧
4. THE Result_Section SHALL 使用分隔线区分输入区域和结果区域

### Requirement 4: 知识库页面布局优化

**User Story:** As a 用户, I want 在知识库页面快速浏览和管理脚本, so that 我可以高效地查找和维护参考脚本。

#### Acceptance Criteria

1. THE UI SHALL 在知识库页面顶部显示统计卡片（脚本总数、品类数量）
2. THE UI SHALL 使用筛选栏固定在列表上方
3. THE UI SHALL 为脚本列表项使用卡片样式而非 expander
4. THE UI SHALL 在每个脚本卡片中显示品类标签、游戏名称、入库时间
5. THE UI SHALL 支持脚本卡片的展开/收起查看详情

### Requirement 5: 项目历史页面布局优化

**User Story:** As a 用户, I want 在项目历史页面快速定位和查看历史脚本, so that 我可以方便地复用和参考之前的工作。

#### Acceptance Criteria

1. THE UI SHALL 在项目历史页面使用左右分栏布局
2. THE UI SHALL 在左侧显示项目列表（客户-项目树形结构）
3. THE UI SHALL 在右侧显示选中项目的详情和历史脚本
4. THE UI SHALL 为历史脚本使用时间线样式展示
5. WHEN 选中项目时 THEN THE UI SHALL 高亮显示当前选中项

### Requirement 6: 设置页面布局优化

**User Story:** As a 用户, I want 在设置页面清晰地管理各项配置, so that 我可以快速找到并修改需要的设置。

#### Acceptance Criteria

1. THE UI SHALL 在设置页面使用垂直 tabs 替代水平 tabs
2. THE UI SHALL 为每个设置分类使用独立的卡片区域
3. THE UI SHALL 在 API 配置区域使用表格展示已有配置列表
4. THE UI SHALL 将新增/编辑配置表单放在配置列表下方

### Requirement 7: 响应式布局支持

**User Story:** As a 用户, I want 在不同屏幕尺寸下获得良好的使用体验, so that 我可以在各种设备上使用工具。

#### Acceptance Criteria

1. WHEN 屏幕宽度小于 1200px 时 THEN THE UI SHALL 将多列布局调整为单列
2. WHEN 屏幕宽度小于 768px 时 THEN THE Sidebar_Navigation SHALL 默认收起
3. THE UI SHALL 为所有卡片组件设置最小宽度以防止内容挤压
4. THE UI SHALL 为文本输入区域设置合理的最小高度

### Requirement 8: 信息层级优化

**User Story:** As a 用户, I want 通过视觉层级快速识别重要信息, so that 我可以高效地获取关键内容。

#### Acceptance Criteria

1. THE Info_Hierarchy SHALL 使用不同字号区分标题层级（H1: 24px, H2: 20px, H3: 16px）
2. THE Info_Hierarchy SHALL 使用颜色区分主要信息和次要信息
3. THE Info_Hierarchy SHALL 为状态信息使用徽章样式（如品类标签、入库状态）
4. THE Info_Hierarchy SHALL 为操作按钮使用主次样式区分（主要操作使用 primary 样式）
