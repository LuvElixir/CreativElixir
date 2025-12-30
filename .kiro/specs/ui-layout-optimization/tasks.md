# Implementation Plan: UI 布局优化

## Overview

采用自顶向下的实现策略，先扩展 CSS 样式模块，再逐页优化布局结构。使用 Python + Streamlit 技术栈，保持现有业务逻辑不变。

## Tasks

- [x] 1. 扩展 CSS 样式模块
  - [x] 1.1 添加卡片组件样式
    - 定义 .ui-card、.ui-card-header 样式
    - 设置 min-width: 300px 防止内容挤压
    - _Requirements: 2.1, 7.3_
  - [x] 1.2 添加徽章组件样式
    - 定义 .ui-badge、.ui-badge-primary、.ui-badge-secondary、.ui-badge-success
    - _Requirements: 8.3_
  - [x] 1.3 添加时间线组件样式
    - 定义 .ui-timeline、.ui-timeline-item 样式
    - _Requirements: 5.4_
  - [x] 1.4 添加信息层级样式
    - 定义 .ui-h1 (24px)、.ui-h2 (20px)、.ui-h3 (16px) 标题样式
    - 定义 .ui-text-secondary 次要文本样式
    - _Requirements: 8.1, 8.2_
  - [x] 1.5 添加响应式断点样式
    - 添加 @media (max-width: 1200px) 多列转单列
    - 添加 @media (max-width: 768px) 卡片最小宽度调整
    - 添加文本输入最小高度 min-height: 80px
    - _Requirements: 7.1, 7.2, 7.4_

- [x] 2. 创建 UI 辅助函数
  - [x] 2.1 实现 render_badge() 函数
    - 接受 text 和 variant 参数
    - 返回徽章 HTML 字符串
    - _Requirements: 8.3_
  - [x] 2.2 实现 render_page_header() 函数
    - 显示项目名称、客户名称
    - 显示生成模型和评审模型信息
    - 未选择项目时显示提示
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Checkpoint - CSS 和辅助函数验证
  - 确保应用可正常启动，样式正确加载

- [x] 4. 脚本生成页布局优化
  - [x] 4.1 重构输入区域为卡片布局
    - 项目信息卡片：项目名称、客户名称、品类
    - 脚本参数卡片：游戏介绍、USP、目标人群
    - 使用 3:1 列比例布局游戏介绍和其他输入
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - [x] 4.2 添加页面头部
    - 调用 render_page_header() 显示状态信息
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 4.3 优化结果展示区域
    - 使用卡片包裹结果表格
    - 添加结果摘要（分镜数量）
    - 操作按钮右对齐
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [ ]* 4.4 编写结果摘要正确性测试
    - **Property 1: 结果摘要显示正确的分镜数量**
    - **Validates: Requirements 3.2**

- [x] 5. 知识库页布局优化
  - [x] 5.1 添加统计卡片区域
    - 脚本总数卡片
    - 品类数量卡片
    - 筛选栏
    - _Requirements: 4.1, 4.2_
  - [x] 5.2 重构脚本列表为卡片样式
    - 每个脚本使用卡片容器
    - 显示品类徽章、游戏名称、入库时间
    - 支持展开/收起查看详情
    - _Requirements: 4.3, 4.4, 4.5_
  - [ ]* 5.3 编写脚本卡片信息完整性测试
    - **Property 2: 脚本卡片包含必要信息**
    - **Validates: Requirements 4.4**

- [x] 6. Checkpoint - 脚本生成页和知识库页验证
  - 确保两个页面布局正确，功能正常

- [x] 7. 项目历史页布局优化
  - [x] 7.1 实现左右分栏布局
    - 左侧 1/3 宽度显示项目列表
    - 右侧 2/3 宽度显示项目详情
    - _Requirements: 5.1_
  - [x] 7.2 实现项目树形列表
    - 按客户分组显示项目
    - 使用 expander 展开客户下的项目
    - 高亮当前选中项目
    - _Requirements: 5.2, 5.5_
  - [x] 7.3 实现项目详情区域
    - 项目信息卡片
    - 历史脚本时间线
    - _Requirements: 5.3, 5.4_

- [x] 8. 设置页布局优化
  - [x] 8.1 实现垂直 tabs 布局
    - 左侧设置菜单（使用 radio 模拟）
    - 右侧设置内容区域
    - _Requirements: 6.1_
  - [x] 8.2 优化 API 配置区域
    - 使用卡片包裹配置区域
    - 配置列表使用表格展示
    - 新增/编辑表单放在列表下方
    - _Requirements: 6.2, 6.3, 6.4_
  - [x] 8.3 优化提示词管理区域
    - 使用卡片包裹
    - _Requirements: 6.2_

- [x] 9. 信息层级优化
  - [x] 9.1 统一按钮样式
    - 主要操作使用 type="primary"
    - 次要操作使用默认样式
    - _Requirements: 8.4_
  - [x] 9.2 应用徽章样式
    - 品类标签使用 primary 徽章
    - 入库状态使用 success/secondary 徽章
    - _Requirements: 8.3_

- [x] 10. Final Checkpoint - 完整功能验证
  - 确保所有页面布局正确
  - 确保原有业务逻辑不受影响
  - 验证响应式布局在不同宽度下正常
  - 如有问题请询问用户

## Notes

- 标记 `*` 的任务为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都引用了具体的需求条款以便追溯
- Checkpoint 任务用于阶段性验证
- 核心业务逻辑保持不变，仅修改 UI 渲染层代码
- 使用 Streamlit 原生组件 + CSS 注入实现布局优化
