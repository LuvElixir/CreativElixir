"""
游戏信息流广告脚本自动化工具 - 主应用入口

基于 Streamlit 构建的 AI 驱动广告脚本生成工具。
深色科技感 SaaS 风格 UI。
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import traceback
from typing import Optional, Tuple
from streamlit_option_menu import option_menu

# 导入核心模块
from src.api_manager import APIManager, APIConfig
from src.rag_system import RAGSystem
from src.project_manager import ProjectManager, Project
from src.script_generator import ScriptGenerator, GenerationInput, parse_script_output

# 页面配置
st.set_page_config(
    page_title="CreativElixir - 游戏广告脚本生成器",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== CSS 注入模块 ====================
def inject_custom_css():
    """
    注入自定义 CSS 样式
    
    实现 SaaS 风格的深色科技感主题
    """
    st.markdown("""
    <style>
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 主应用背景 */
    .stApp {
        background-color: #111827;
    }
    
    /* ==================== 卡片组件样式 ==================== */
    .ui-card {
        background-color: #1f2937;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #374151;
        margin-bottom: 16px;
    }
    
    .ui-card-header {
        font-size: 16px;
        font-weight: 600;
        color: #f9fafb;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #374151;
    }
    
    /* ==================== 徽章组件样式 ==================== */
    .ui-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .ui-badge-primary {
        background-color: #6366f1;
        color: #ffffff;
    }
    
    .ui-badge-secondary {
        background-color: #374151;
        color: #9ca3af;
    }
    
    .ui-badge-success {
        background-color: #10b981;
        color: #ffffff;
    }
    
    /* ==================== 时间线组件样式 ==================== */
    .ui-timeline {
        position: relative;
        padding-left: 24px;
    }
    
    .ui-timeline::before {
        content: '';
        position: absolute;
        left: 8px;
        top: 0;
        bottom: 0;
        width: 2px;
        background-color: #374151;
    }
    
    .ui-timeline-item {
        position: relative;
        padding-bottom: 16px;
    }
    
    .ui-timeline-item::before {
        content: '';
        position: absolute;
        left: -20px;
        top: 4px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #6366f1;
    }
    
    /* ==================== 信息层级样式 ==================== */
    .ui-h1 {
        font-size: 24px;
        font-weight: 700;
        color: #f9fafb;
    }
    
    .ui-h2 {
        font-size: 20px;
        font-weight: 600;
        color: #f9fafb;
    }
    
    .ui-h3 {
        font-size: 16px;
        font-weight: 500;
        color: #e5e7eb;
    }
    
    .ui-text-secondary {
        color: #9ca3af;
        font-size: 14px;
    }
    
    /* ==================== 响应式断点样式 ==================== */
    @media (max-width: 1200px) {
        .responsive-cols {
            flex-direction: column;
        }
        
        .ui-card {
            min-width: auto;
        }
    }
    
    @media (max-width: 768px) {
        .ui-card {
            min-width: auto;
            padding: 16px;
        }
        
        .ui-h1 {
            font-size: 20px;
        }
        
        .ui-h2 {
            font-size: 18px;
        }
        
        .ui-h3 {
            font-size: 14px;
        }
    }
    
    /* 文本输入最小高度 */
    .stTextArea textarea {
        min-height: 80px;
    }
    
    /* 输入组件圆角 */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }
    
    /* 按钮样式优化 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* 主按钮样式 */
    .stButton > button[kind="primary"] {
        background-color: #6366f1;
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #4f46e5;
    }
    
    /* 统计卡片样式 */
    .stat-card {
        background-color: #1f2937;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #374151;
        text-align: center;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #6366f1;
    }
    
    .stat-label {
        font-size: 14px;
        color: #9ca3af;
        margin-top: 4px;
    }
    
    /* ==================== 辩论模式样式 ==================== */
    .debate-container h3 {
        background-color: #374151;
        border-left: 4px solid #6366f1;
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 16px;
        margin-top: 20px;
        display: flex;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)


# ==================== UI 辅助函数 ====================
def render_badge(text: str, variant: str = "primary") -> str:
    """渲染徽章组件"""
    return f'<span class="ui-badge ui-badge-{variant}">{text}</span>'


def render_page_header():
    """渲染页面头部状态信息"""
    project = st.session_state.get("current_project")
    api_manager = st.session_state.get("api_manager")
    gen_config = api_manager.load_config() if api_manager else None
    rev_manager = st.session_state.get("review_api_manager")
    
    header_parts = []
    
    if project:
        header_parts.append(f"**项目:** {project.client_name} / {project.project_name}")
    else:
        header_parts.append("**项目:** 未选择项目")
    
    if gen_config:
        model_info = f"**生成:** {gen_config.model_id}"
        if rev_manager:
            rev_config = rev_manager.load_config()
            if rev_config:
                model_info += f" | **评审:** {rev_config.model_id}"
        header_parts.append(model_info)
    
    st.markdown(" · ".join(header_parts))


# ==================== 导航组件 ====================
def render_navigation() -> str:
    """渲染侧边栏导航菜单"""
    with st.sidebar:
        selected = option_menu(
            menu_title="CreativElixir",
            options=["脚本生成", "知识库", "项目历史", "设置"],
            icons=["pen-tool", "database", "clock-history", "gear"],
            menu_icon="robot",
            default_index=0,
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent"
                },
                "icon": {
                    "color": "#818cf8",
                    "font-size": "18px"
                },
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "5px",
                    "--hover-color": "#374151"
                },
                "nav-link-selected": {
                    "background-color": "#6366f1"
                }
            }
        )
    return selected


# ==================== 错误处理工具函数 ====================
def display_error(message: str, details: Optional[str] = None):
    """显示用户友好的错误信息"""
    st.error(message)
    if details:
        with st.expander("查看详细信息"):
            st.code(details)


def display_warning(message: str):
    """显示警告信息"""
    st.warning(message)


def display_success(message: str):
    """显示成功信息"""
    st.success(message)


def display_info(message: str):
    """显示提示信息"""
    st.info(message)


def validate_api_config(api_manager: APIManager) -> Tuple[bool, str]:
    """验证 API 配置是否有效"""
    config = api_manager.load_config()
    if not config:
        return False, "未配置 API，请先在设置中配置 API"
    
    is_valid, error_msg = config.is_valid()
    if not is_valid:
        return False, f"API 配置无效: {error_msg}"
    
    return True, ""


def validate_generation_input(game_intro: str, usp: str, target_audience: str, theme: str, gameplay: str) -> Tuple[bool, str]:
    """验证脚本生成输入"""
    errors = []
    
    if not game_intro or not game_intro.strip():
        errors.append("游戏介绍不能为空")
    if not usp or not usp.strip():
        errors.append("独特卖点 (USP) 不能为空")
    if not target_audience or not target_audience.strip():
        errors.append("目标人群不能为空")
    if not theme or not theme.strip():
        errors.append("请选择游戏题材")
    if not gameplay or not gameplay.strip():
        errors.append("请选择核心玩法")
    
    if errors:
        return False, "、".join(errors)
    
    return True, ""


# ==================== Session State 初始化 ====================
def init_session_state():
    """初始化会话状态"""
    if "api_manager" not in st.session_state:
        try:
            st.session_state.api_manager = APIManager()
        except Exception as e:
            st.session_state.api_manager = None
            st.session_state.init_error_api = str(e)
    
    if "rag_system" not in st.session_state:
        try:
            api_manager = st.session_state.get("api_manager")
            st.session_state.rag_system = RAGSystem(api_manager=api_manager)
        except Exception as e:
            st.session_state.rag_system = None
            st.session_state.init_error_rag = str(e)
    
    if "project_manager" not in st.session_state:
        try:
            st.session_state.project_manager = ProjectManager()
        except Exception as e:
            st.session_state.project_manager = None
            st.session_state.init_error_project = str(e)
    
    if st.session_state.api_manager:
        from src.prompts import PromptManager
        PromptManager.set_api_manager(st.session_state.api_manager)
    
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "generated_script" not in st.session_state:
        st.session_state.generated_script = None
    if "generation_output" not in st.session_state:
        st.session_state.generation_output = None
    if "last_error" not in st.session_state:
        st.session_state.last_error = None
    if "review_api_manager" not in st.session_state:
        st.session_state.review_api_manager = None
    if "selected_review_config" not in st.session_state:
        st.session_state.selected_review_config = "使用生成模型"
    if "selected_setting" not in st.session_state:
        st.session_state.selected_setting = "API 配置"
    if "selected_history_project" not in st.session_state:
        st.session_state.selected_history_project = None


def check_system_health() -> Tuple[bool, list]:
    """检查系统各模块健康状态"""
    errors = []
    
    if st.session_state.api_manager is None:
        errors.append(f"API 管理器初始化失败: {st.session_state.get('init_error_api', '未知错误')}")
    
    if st.session_state.rag_system is None:
        errors.append(f"知识库系统初始化失败: {st.session_state.get('init_error_rag', '未知错误')}")
    
    if st.session_state.project_manager is None:
        errors.append(f"项目管理器初始化失败: {st.session_state.get('init_error_project', '未知错误')}")
    
    return len(errors) == 0, errors


init_session_state()


# ==================== 脚本生成页面 ====================
def render_script_generation_page():
    """渲染脚本生成页面"""
    st.markdown("### 脚本生成")
    
    is_healthy, errors = check_system_health()
    if not is_healthy:
        for error in errors:
            display_error(error)
        return
    
    api_manager = st.session_state.api_manager
    is_valid, error_msg = validate_api_config(api_manager)
    if not is_valid:
        display_warning(error_msg)
        return
    
    render_page_header()
    
    # 获取题材和玩法列表
    rag_system = st.session_state.rag_system
    try:
        themes = rag_system.list_available_themes()
        gameplays = rag_system.list_available_gameplays()
    except Exception:
        themes = ["魔幻", "传奇", "三国", "历史", "战争", "武侠", "仙侠", "二次元", "现代", "都市"]
        gameplays = ["休闲消除", "网赚", "放置挂机", "益智解谜", "传奇ARPG", "卡牌", "射击", "SLG", "MMO"]
    
    # 添加"其他"选项
    themes_with_other = themes + ["其他"]
    gameplays_with_other = gameplays + ["其他"]
    
    # ==================== 项目信息卡片 ====================
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">项目信息</div>', unsafe_allow_html=True)
    
    proj_col1, proj_col2 = st.columns([1, 1])
    with proj_col1:
        project_name = st.text_input(
            "项目/游戏名称",
            value=st.session_state.current_project.project_name if st.session_state.current_project else "",
            placeholder="请输入项目或游戏名称..."
        )
    with proj_col2:
        client_name = st.text_input(
            "客户名称",
            value=st.session_state.current_project.client_name if st.session_state.current_project else "",
            placeholder="请输入客户名称..."
        )
    
    # 题材和玩法选择
    theme_col, gameplay_col = st.columns([1, 1])
    with theme_col:
        theme = st.selectbox(
            "游戏题材",
            themes_with_other,
            index=0,
            help="选择游戏的题材类型，影响文案风格和卖点侧重"
        )
    with gameplay_col:
        gameplay = st.selectbox(
            "核心玩法",
            gameplays_with_other,
            index=0,
            help="选择游戏的核心玩法，影响文案的功能卖点"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== 脚本参数卡片 ====================
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">脚本参数</div>', unsafe_allow_html=True)
    
    param_col1, param_col2 = st.columns([3, 1])
    
    with param_col1:
        game_intro = st.text_area(
            "游戏介绍",
            height=150,
            placeholder="请输入游戏的基本介绍，包括游戏类型、玩法特点等...",
            value=st.session_state.current_project.game_intro if st.session_state.current_project else ""
        )
    
    with param_col2:
        usp = st.text_area(
            "独特卖点 (USP)",
            height=70,
            placeholder="请输入游戏的独特卖点...",
            value=st.session_state.current_project.usp if st.session_state.current_project else ""
        )
        target_audience = st.text_area(
            "目标人群",
            height=70,
            placeholder="请描述目标用户群体...",
            value=st.session_state.current_project.target_audience if st.session_state.current_project else ""
        )
    
    # 评审模型选择
    try:
        all_configs = api_manager.get_all_configs()
        config_names = [config.name for config in all_configs]
        review_options = ["使用生成模型"] + config_names
        
        current_review_selection = st.session_state.get("selected_review_config", "使用生成模型")
        if current_review_selection not in review_options:
            current_review_selection = "使用生成模型"
        
        review_col1, review_col2, review_col3 = st.columns([2, 1, 1])
        with review_col3:
            selected_review_model = st.selectbox(
                "评审模型",
                review_options,
                index=review_options.index(current_review_selection),
                key="review_model_main"
            )
        
        if selected_review_model == "使用生成模型":
            st.session_state.review_api_manager = None
            st.session_state.selected_review_config = "使用生成模型"
        else:
            try:
                review_api_manager = APIManager()
                review_api_manager.switch_config(selected_review_model)
                st.session_state.review_api_manager = review_api_manager
                st.session_state.selected_review_config = selected_review_model
            except Exception:
                st.session_state.review_api_manager = None
                st.session_state.selected_review_config = "使用生成模型"
    except Exception:
        st.caption("请先配置 API")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 生成按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button("生成脚本", use_container_width=True, type="primary")
    
    # 生成逻辑
    if generate_btn:
        is_valid, error_msg = validate_generation_input(game_intro, usp, target_audience, theme, gameplay)
        if not is_valid:
            display_error(error_msg)
            return
        
        if not project_name or not project_name.strip():
            display_error("请输入项目/游戏名称")
            return
        if not client_name or not client_name.strip():
            display_error("请输入客户名称")
            return
        
        # 组合 category（用于兼容现有逻辑）
        # 优先使用玩法作为主分类，题材作为辅助
        category = gameplay if gameplay != "其他" else theme
        
        # 自动保存/更新项目信息
        try:
            project_manager = st.session_state.project_manager
            existing_project = project_manager.get_project(client_name.strip(), project_name.strip())
            
            if existing_project:
                existing_project.game_intro = game_intro
                existing_project.usp = usp
                existing_project.target_audience = target_audience
                existing_project.category = category
                # 保存题材和玩法到项目（如果支持）
                if hasattr(existing_project, 'theme'):
                    existing_project.theme = theme
                if hasattr(existing_project, 'gameplay'):
                    existing_project.gameplay = gameplay
                project_manager.update_project(existing_project)
                st.session_state.current_project = existing_project
            else:
                new_project = project_manager.create_project(client_name.strip(), project_name.strip())
                new_project.game_intro = game_intro
                new_project.usp = usp
                new_project.target_audience = target_audience
                new_project.category = category
                project_manager.update_project(new_project)
                st.session_state.current_project = new_project
                display_success(f"项目 '{client_name}/{project_name}' 已自动保存")
        except Exception as e:
            display_warning(f"保存项目信息失败: {str(e)}")
        
        # 使用综合特征
        input_data = GenerationInput(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category,
            theme=theme if theme != "其他" else None,
            gameplay=gameplay if gameplay != "其他" else None
        )
        
        try:
            generator = ScriptGenerator(
                api_manager=api_manager,
                rag_system=st.session_state.rag_system,
                review_api_manager=st.session_state.get("review_api_manager")
            )
        except Exception as e:
            display_error("初始化脚本生成器失败", str(e))
            return
        
        # 使用 st.status 包裹生成过程
        with st.status("正在构建创意...", expanded=True) as status:
            full_output = ""
            output = None
            
            # 辩论容器状态变量
            debate_expander_created = False
            debate_expander = None
            debate_container = None
            debate_content = ""
            
            try:
                status.write("正在检索同品类参考脚本...")
                status.write("正在生成脚本初稿...")
                
                gen = generator.generate(input_data)
                
                # 遍历生成器获取所有输出，并捕获最终返回值
                try:
                    while True:
                        chunk = next(gen)
                        
                        # 检测评审阶段并创建辩论容器
                        if "[REVIEW]" in chunk:
                            if not debate_expander_created:
                                status.write("正在评审脚本质量...")
                                debate_expander = st.expander(
                                    "⚔️ 评审委员会激烈辩论中 (思维链)...", 
                                    expanded=True
                                )
                                debate_container = debate_expander.empty()
                                debate_expander_created = True
                            
                            # 提取评审内容并更新
                            review_text = chunk.replace("[REVIEW]", "")
                            debate_content += review_text
                            debate_container.markdown(debate_content)
                        
                        full_output += chunk
                except StopIteration as e:
                    # Generator 的 return 值在 StopIteration.value 中
                    output = e.value
                
                status.write("正在优化脚本...")
                
                # 如果没有获取到 output，使用 parse_script_output 解析
                if output is None:
                    output = parse_script_output(full_output)
                
                st.session_state.generated_script = full_output
                st.session_state.generation_output = output
                st.session_state.last_error = None
                
                status.update(label="创意构建完成!", state="complete", expanded=False)
                
            except Exception as e:
                st.session_state.last_error = str(e)
                status.update(label="生成失败", state="error", expanded=True)
                display_error("脚本生成失败", str(e))
        
        # 生成完成后刷新页面以显示结果（放在 status 块外面）
        if st.session_state.generation_output:
            st.rerun()
    
    # ==================== 结果展示区域 ====================
    if st.session_state.generation_output:
        st.markdown("---")
        
        output = st.session_state.generation_output
        
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="ui-card-header">生成结果</div>', unsafe_allow_html=True)
        
        if output.is_valid():
            storyboard_count = len(output.storyboard)
            st.markdown(f"已生成 **{storyboard_count}** 个分镜")
            
            max_len = max(
                len(output.storyboard),
                len(output.voiceover),
                len(output.design_intent)
            )
            
            storyboard_padded = output.storyboard + [""] * (max_len - len(output.storyboard))
            voiceover_padded = output.voiceover + [""] * (max_len - len(output.voiceover))
            design_intent_padded = output.design_intent + [""] * (max_len - len(output.design_intent))
            
            df = pd.DataFrame({
                "分镜": storyboard_padded,
                "口播": voiceover_padded,
                "设计意图": design_intent_padded
            })
            
            # 双视图 Tabs
            tab_preview, tab_edit = st.tabs(["沉浸预览", "编辑修正"])
            
            with tab_preview:
                # 沉浸预览模式 - 美观渲染 Markdown
                if not df.empty:
                    for idx, row in df.iterrows():
                        # 跳过空行
                        if not row.get("分镜", "").strip() and not row.get("口播", "").strip():
                            continue
                        
                        st.markdown(f'<div class="ui-card">', unsafe_allow_html=True)
                        st.markdown(f"#### 分镜 {idx + 1}")
                        
                        p_col1, p_col2, p_col3 = st.columns(3)
                        
                        with p_col1:
                            st.caption("画面分镜")
                            st.markdown(row.get("分镜", "") or "-")
                        
                        with p_col2:
                            st.caption("口播台词")
                            st.markdown(row.get("口播", "") or "-")
                        
                        with p_col3:
                            st.caption("设计意图")
                            st.markdown(row.get("设计意图", "") or "-")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("暂无内容")
            
            with tab_edit:
                # 编辑修正模式 - 原始数据编辑器
                st.caption("提示: 双击单元格可编辑 Markdown 原始内容")
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "分镜": st.column_config.TextColumn("分镜", width="medium"),
                        "口播": st.column_config.TextColumn("口播", width="large"),
                        "设计意图": st.column_config.TextColumn("设计意图", width="medium")
                    },
                    key="script_editor"
                )
            
            # 操作按钮 - 放在 Tabs 下方
            st.markdown("---")
            btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
            with btn_col2:
                if st.button("导出", use_container_width=True, type="secondary"):
                    try:
                        # 使用编辑后的数据（如果有）
                        export_df = edited_df if 'edited_df' in dir() else df
                        csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="下载 CSV",
                            data=csv_data,
                            file_name="script_output.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    except Exception as e:
                        display_error("导出失败", str(e))
            with btn_col3:
                if st.button("入库", use_container_width=True, type="primary"):
                    try:
                        archive_category = category if 'category' in dir() else (
                            st.session_state.current_project.category if st.session_state.current_project else "SLG"
                        )
                        
                        # 使用编辑后的数据（如果有）
                        final_df = edited_df if 'edited_df' in dir() else df
                        edited_storyboard = [s for s in final_df["分镜"].tolist() if str(s).strip()]
                        edited_voiceover = [v for v in final_df["口播"].tolist() if str(v).strip()]
                        edited_design_intent = [d for d in final_df["设计意图"].tolist() if str(d).strip()]
                        
                        rag_system = st.session_state.rag_system
                        doc_id = rag_system.add_script(
                            content=output.raw_content,
                            category=archive_category,
                            metadata={
                                "game_name": st.session_state.current_project.project_name if st.session_state.current_project else "",
                                "performance": "用户生成",
                                "source": "user_archive"
                            }
                        )
                        
                        if st.session_state.current_project:
                            st.session_state.project_manager.add_script_to_history(
                                client_name=st.session_state.current_project.client_name,
                                project_name=st.session_state.current_project.project_name,
                                script=output.raw_content,
                                parsed_output={
                                    "storyboard": edited_storyboard,
                                    "voiceover": edited_voiceover,
                                    "design_intent": edited_design_intent
                                }
                            )
                        
                        display_success("脚本已入库!")
                    except Exception as e:
                        display_error("入库失败", str(e))
        else:
            st.markdown("**原始输出:**")
            st.text(output.raw_content)
            display_warning("脚本格式解析失败，显示原始内容。您可以手动复制并编辑。")
        
        st.markdown('</div>', unsafe_allow_html=True)


# ==================== 知识库页面 ====================
def render_knowledge_base_page():
    """渲染知识库页面"""
    st.markdown("### 知识库")
    
    rag_system = st.session_state.rag_system
    
    if rag_system is None:
        display_error("知识库系统未初始化")
        return
    
    try:
        categories = rag_system.get_categories()
    except Exception as e:
        display_error("获取品类列表失败", str(e))
        categories = []
    
    try:
        all_scripts = []
        for cat in categories:
            all_scripts.extend(rag_system.get_scripts_by_category(cat))
        total_script_count = len(all_scripts)
    except Exception as e:
        display_error("获取脚本统计失败", str(e))
        total_script_count = 0
    
    # ==================== 统计卡片区域 ====================
    stat_col1, stat_col2, stat_col3 = st.columns([1, 1, 2])
    
    with stat_col1:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.metric("脚本总数", total_script_count)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.metric("品类数量", len(categories))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_col3:
        selected_category = st.selectbox(
            "筛选品类", 
            ["全部"] + categories, 
            key="kb_category_filter"
        )
    
    st.markdown("---")
    
    # ==================== 快速采集面板 ====================
    with st.expander("快速采集 (AI 智能打标)", expanded=False):
        raw_text = st.text_area(
            "粘贴广告文案",
            height=200,
            placeholder="在此粘贴广告脚本文案...",
            key="quick_capture_text"
        )
        
        if st.button("AI 分析并入库", type="primary", key="quick_capture_btn"):
            if not raw_text or not raw_text.strip():
                display_warning("请先粘贴广告文案")
            elif rag_system is None:
                display_error("知识库系统未初始化")
            else:
                with st.spinner("AI 正在阅读并打标签..."):
                    try:
                        success, message, metadata = rag_system.auto_ingest_script(raw_text)
                        
                        if success:
                            category_result = metadata.category if metadata else "其他"
                            display_success(f"入库成功! 已归档至品类: {category_result}")
                            
                            if metadata:
                                st.markdown("**提取的元数据:**")
                                import json
                                metadata_json = json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2)
                                st.code(metadata_json, language="json")
                        else:
                            display_error(f"入库失败: {message}")
                    except Exception as e:
                        display_error(f"处理异常: {str(e)}")
    
    # 获取筛选后的脚本列表
    try:
        if selected_category == "全部":
            scripts = all_scripts
        else:
            scripts = rag_system.get_scripts_by_category(selected_category)
    except Exception as e:
        display_error("获取脚本列表失败", str(e))
        scripts = []
    
    # ==================== 脚本卡片列表 ====================
    if scripts:
        for i, script in enumerate(scripts):
            render_script_card(script, i, rag_system)
    else:
        display_info("暂无脚本数据")
    
    st.markdown("---")
    
    # ==================== 数据管理区域 ====================
    st.markdown("#### 数据管理")
    
    mgmt_col1, mgmt_col2 = st.columns([1, 1])
    
    with mgmt_col1:
        if st.button("导出知识库", use_container_width=True, type="secondary"):
            with st.spinner("正在导出..."):
                try:
                    export_path = "./data/knowledge_base_export"
                    success, result = rag_system.export_knowledge_base(export_path)
                    if success:
                        with open(result, "rb") as f:
                            st.download_button(
                                label="下载导出文件",
                                data=f,
                                file_name="knowledge_base.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                    else:
                        display_error(result)
                except Exception as e:
                    display_error("导出失败", str(e))
    
    with mgmt_col2:
        with st.expander("批量导入工具", expanded=False):
            st.caption("通过 ZIP 文件批量导入脚本到知识库")
            uploaded = st.file_uploader("选择 ZIP 文件", type=["zip"], key="kb_tab_import")
            if uploaded:
                if st.button("确认导入", use_container_width=True, type="primary"):
                    with st.spinner("正在导入..."):
                        try:
                            import_path = Path("./data/_temp_import.zip")
                            import_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(import_path, "wb") as f:
                                f.write(uploaded.getvalue())
                            
                            success, msg = rag_system.import_knowledge_base(str(import_path))
                            
                            if import_path.exists():
                                import_path.unlink()
                            
                            if success:
                                display_success(msg)
                                st.rerun()
                            else:
                                display_error(msg)
                        except Exception as e:
                            display_error("导入失败", str(e))


def render_script_card(script, index: int, rag_system):
    """渲染单个脚本卡片"""
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        game_name = script.metadata.game_name or "未命名"
        st.markdown(f'<span class="ui-h3">{game_name}</span>', unsafe_allow_html=True)
    
    with header_col2:
        badge_html = render_badge(script.category, "primary")
        st.markdown(badge_html, unsafe_allow_html=True)
    
    archived_at = script.metadata.archived_at or "未知"
    st.markdown(
        f'<span class="ui-text-secondary">入库时间: {archived_at}</span>', 
        unsafe_allow_html=True
    )
    
    with st.expander("查看详情"):
        st.markdown(f"**来源:** {script.metadata.source}")
        st.markdown("---")
        st.markdown("**内容预览:**")
        content_preview = script.content[:500] + "..." if len(script.content) > 500 else script.content
        st.text(content_preview)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            if st.button("删除", key=f"delete_script_{script.id}", type="secondary"):
                try:
                    if rag_system.delete_script(script.id):
                        display_success("脚本已删除")
                        st.rerun()
                    else:
                        display_error("删除失败，脚本可能不存在")
                except Exception as e:
                    display_error("删除脚本时发生错误", str(e))
    
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 项目历史页面 ====================
def render_project_history_page():
    """渲染项目历史页面 - 左右分栏布局"""
    st.markdown("### 项目历史")
    
    project_manager = st.session_state.project_manager
    
    if project_manager is None:
        display_error("项目管理器未初始化")
        return
    
    try:
        clients = project_manager.list_clients()
    except Exception as e:
        display_error("获取客户列表失败", str(e))
        clients = []
    
    if not clients:
        display_info("暂无项目，请先在脚本生成页面创建项目")
        return
    
    # 左右分栏布局
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        render_project_tree(project_manager, clients)
    
    with right_col:
        render_project_detail_area(project_manager)


def render_project_tree(project_manager, clients: list):
    """渲染项目树形列表"""
    st.markdown("#### 项目列表")
    
    for client in clients:
        try:
            projects = project_manager.get_projects_by_client(client)
        except Exception as e:
            display_error(f"获取 {client} 的项目列表失败", str(e))
            continue
        
        if not projects:
            continue
        
        with st.expander(f"{client} ({len(projects)})", expanded=True):
            for project in projects:
                project_key = f"{client}/{project.project_name}"
                is_selected = st.session_state.get("selected_history_project") == project_key
                
                if is_selected:
                    if st.button(
                        f"● {project.project_name}",
                        key=f"proj_{project_key}",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.session_state.selected_history_project = project_key
                        st.rerun()
                else:
                    if st.button(
                        project.project_name,
                        key=f"proj_{project_key}",
                        use_container_width=True
                    ):
                        st.session_state.selected_history_project = project_key
                        st.rerun()


def render_project_detail_area(project_manager):
    """渲染项目详情区域"""
    selected = st.session_state.get("selected_history_project")
    
    if not selected:
        st.info("请从左侧选择项目查看详情")
        return
    
    try:
        client, project_name = selected.split("/", 1)
        project = project_manager.get_project(client, project_name)
    except Exception as e:
        display_error("加载项目失败", str(e))
        return
    
    if not project:
        st.warning("项目不存在或已被删除")
        st.session_state.selected_history_project = None
        return
    
    render_project_info_card(project)
    render_scripts_timeline(project)


def render_project_info_card(project):
    """渲染项目信息卡片"""
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="ui-card-header">{project.project_name}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**客户:** {project.client_name}")
        category_badge = render_badge(project.category or "未设置", "primary")
        st.markdown(f"**品类:** {category_badge}", unsafe_allow_html=True)
    with col2:
        st.markdown(f"**创建时间:** {project.created_at[:10]}")
        script_count = len(project.scripts_history) if project.scripts_history else 0
        st.markdown(f"**脚本数:** {script_count}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_scripts_timeline(project):
    """渲染历史脚本时间线"""
    st.markdown("#### 历史脚本")
    
    if not project.scripts_history:
        display_info("暂无历史脚本")
        return
    
    st.markdown('<div class="ui-timeline">', unsafe_allow_html=True)
    
    for record in reversed(project.scripts_history):
        render_timeline_item(record)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_timeline_item(record):
    """渲染时间线项"""
    st.markdown('<div class="ui-timeline-item">', unsafe_allow_html=True)
    
    status_badge = render_badge("已入库", "success") if record.is_archived else render_badge("未入库", "secondary")
    st.markdown(
        f"**版本 {record.version}** · {record.created_at[:10]} {status_badge}",
        unsafe_allow_html=True
    )
    
    with st.expander("查看内容"):
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(f"**创建时间:** {record.created_at}")
        with meta_col2:
            detail_status_badge = render_badge("已入库", "success") if record.is_archived else render_badge("未入库", "secondary")
            st.markdown(f"**入库状态:** {detail_status_badge}", unsafe_allow_html=True)
        
        st.markdown("---")
        
        if record.parsed_output:
            try:
                from src.script_generator import ScriptOutput
                output = ScriptOutput(
                    storyboard=record.parsed_output.get("storyboard", []),
                    voiceover=record.parsed_output.get("voiceover", []),
                    design_intent=record.parsed_output.get("design_intent", []),
                    raw_content=record.content
                )
                if output.is_valid():
                    st.markdown(output.to_markdown_table())
                else:
                    st.markdown("**脚本内容:**")
                    st.text(record.content)
            except Exception:
                st.markdown("**脚本内容:**")
                st.text(record.content)
        else:
            st.markdown("**脚本内容:**")
            content_preview = record.content[:300] + "..." if len(record.content) > 300 else record.content
            st.text(content_preview)
    
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 设置页面 ====================
def render_settings_page():
    """渲染设置页面 - 垂直 Tabs 布局"""
    st.markdown("## 设置")
    
    left_col, right_col = st.columns([1, 3])
    
    with left_col:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="ui-card-header">设置菜单</div>', unsafe_allow_html=True)
        
        settings_options = ["API 配置", "提示词管理"]
        selected_setting = st.radio(
            "设置项",
            settings_options,
            index=settings_options.index(st.session_state.selected_setting) if st.session_state.selected_setting in settings_options else 0,
            label_visibility="collapsed",
            key="settings_menu_radio"
        )
        
        if selected_setting != st.session_state.selected_setting:
            st.session_state.selected_setting = selected_setting
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        if st.session_state.selected_setting == "API 配置":
            render_api_settings_card()
        elif st.session_state.selected_setting == "提示词管理":
            render_prompt_settings_card()


def render_api_settings_card():
    """渲染 API 配置卡片"""
    api_manager = st.session_state.api_manager
    
    if api_manager is None:
        display_error("API 管理器未初始化", st.session_state.get('init_error_api'))
        return
    
    try:
        all_configs = api_manager.get_all_configs()
        current_config = api_manager.load_config()
        active_config_name = api_manager.get_active_config_name()
    except Exception as e:
        display_error("加载 API 配置失败", str(e))
        all_configs = []
        current_config = None
        active_config_name = "default"
    
    # 配置列表卡片
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">API 配置</div>', unsafe_allow_html=True)
    
    if all_configs:
        st.markdown("#### 已有配置")
        
        config_data = []
        for config in all_configs:
            status = "当前" if config.name == active_config_name else ""
            embedding_info = config.embedding_model if config.has_embedding_config() else "未配置"
            config_data.append({
                "配置名称": config.name,
                "模型": config.model_id,
                "Embedding": embedding_info,
                "状态": status
            })
        
        df = pd.DataFrame(config_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        config_names = [config.name for config in all_configs]
        
        if active_config_name not in config_names and config_names:
            active_config_name = config_names[0]
        
        with col1:
            selected_config_name = st.selectbox(
                "选择配置",
                config_names,
                index=config_names.index(active_config_name) if active_config_name in config_names else 0,
                key="settings_config_select"
            )
        
        with col2:
            if st.button("切换到此配置", key="settings_switch_config", use_container_width=True, type="primary"):
                if selected_config_name != active_config_name:
                    try:
                        success, msg = api_manager.switch_config(selected_config_name)
                        if success:
                            if st.session_state.rag_system:
                                st.session_state.rag_system.update_api_manager(api_manager)
                            display_success(f"已切换到配置: {selected_config_name}")
                            st.rerun()
                        else:
                            display_error(f"切换失败: {msg}")
                    except Exception as e:
                        display_error("切换配置时发生错误", str(e))
                else:
                    display_info("当前已是此配置")
        
        with col3:
            if len(all_configs) > 1:
                if st.button("删除配置", key="settings_delete_config", use_container_width=True, type="secondary"):
                    try:
                        success, msg = api_manager.delete_config(selected_config_name)
                        if success:
                            display_success("配置已删除")
                            st.rerun()
                        else:
                            display_error(f"删除失败: {msg}")
                    except Exception as e:
                        display_error("删除配置时发生错误", str(e))
    else:
        display_warning("未配置 API，请添加配置")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 新增/编辑配置表单卡片
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">添加/编辑配置</div>', unsafe_allow_html=True)
    
    with st.form("settings_api_config_form"):
        edit_config = None
        if all_configs and current_config:
            edit_config = current_config
        
        col1, col2 = st.columns(2)
        
        with col1:
            config_name = st.text_input(
                "配置名称",
                value=edit_config.name if edit_config else ""
            )
            api_key = st.text_input(
                "API Key",
                value=edit_config.api_key if edit_config else "",
                type="password"
            )
        
        with col2:
            base_url = st.text_input(
                "Base URL",
                value=edit_config.base_url if edit_config else "https://api.openai.com/v1"
            )
            model_id = st.text_input(
                "Model ID",
                value=edit_config.model_id if edit_config else "gpt-4"
            )
        
        st.markdown("---")
        st.markdown("#### Embedding 模型 (知识库向量检索)")
        
        from src.api_manager import EMBEDDING_MODELS
        
        current_embedding_provider = ""
        current_embedding_model = ""
        if edit_config and edit_config.embedding_model:
            emb_url = edit_config.embedding_base_url or ""
            if "volces.com" in emb_url or "ark" in emb_url:
                current_embedding_provider = "doubao"
            elif "siliconflow" in emb_url:
                current_embedding_provider = "siliconflow"
            else:
                current_embedding_provider = "openai"
            current_embedding_model = edit_config.embedding_model
        
        embedding_providers = ["不使用"] + list(EMBEDDING_MODELS.keys())
        provider_names = ["不使用"] + [EMBEDDING_MODELS[k]["name"] for k in EMBEDDING_MODELS.keys()]
        
        provider_idx = 0
        if current_embedding_provider in embedding_providers:
            provider_idx = embedding_providers.index(current_embedding_provider)
        
        emb_col1, emb_col2 = st.columns(2)
        
        with emb_col1:
            selected_provider_name = st.selectbox(
                "Embedding 提供商",
                provider_names,
                index=provider_idx
            )
        
        selected_provider = ""
        if selected_provider_name != "不使用":
            for k, v in EMBEDDING_MODELS.items():
                if v["name"] == selected_provider_name:
                    selected_provider = k
                    break
        
        embedding_model = ""
        embedding_base_url = ""
        embedding_api_key = ""
        
        if selected_provider and selected_provider in EMBEDDING_MODELS:
            provider_info = EMBEDDING_MODELS[selected_provider]
            model_options = provider_info["models"]
            model_names = [m["name"] for m in model_options]
            model_ids = [m["id"] for m in model_options]
            
            model_idx = 0
            if current_embedding_model in model_ids:
                model_idx = model_ids.index(current_embedding_model)
            
            with emb_col2:
                selected_model_name = st.selectbox(
                    "Embedding 模型",
                    model_names,
                    index=model_idx
                )
            
            for m in model_options:
                if m["name"] == selected_model_name:
                    embedding_model = m["id"]
                    break
            
            embedding_base_url = provider_info["base_url"]
            
            st.caption(f"API 地址: {embedding_base_url}")
            
            embedding_api_key = st.text_input(
                "Embedding API Key",
                value=edit_config.embedding_api_key if edit_config else "",
                type="password"
            )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            test_btn = st.form_submit_button("测试连接", use_container_width=True)
        with col3:
            save_btn = st.form_submit_button("保存配置", use_container_width=True)
    
    if save_btn:
        if not config_name or not config_name.strip():
            display_error("配置名称不能为空")
        elif not api_key or not api_key.strip():
            display_error("API Key 不能为空")
        elif not base_url or not base_url.strip():
            display_error("Base URL 不能为空")
        elif not model_id or not model_id.strip():
            display_error("Model ID 不能为空")
        else:
            try:
                config = APIConfig(
                    api_key=api_key.strip(),
                    base_url=base_url.strip(),
                    model_id=model_id.strip(),
                    name=config_name.strip(),
                    embedding_model=embedding_model,
                    embedding_base_url=embedding_base_url,
                    embedding_api_key=embedding_api_key.strip() if embedding_api_key else ""
                )
                success, msg = api_manager.save_config(config)
                if success:
                    api_manager.switch_config(config_name.strip())
                    if st.session_state.rag_system:
                        st.session_state.rag_system.update_api_manager(api_manager)
                    display_success("配置保存成功并已激活!")
                    st.rerun()
                else:
                    display_error(f"保存失败: {msg}")
            except Exception as e:
                display_error("保存配置时发生错误", str(e))
    
    if test_btn:
        if not api_key or not base_url or not model_id:
            display_error("请先填写完整的 API 配置")
        else:
            with st.spinner("正在测试连接..."):
                try:
                    config = APIConfig(
                        api_key=api_key.strip(),
                        base_url=base_url.strip(),
                        model_id=model_id.strip(),
                        name=config_name.strip()
                    )
                    original_config = api_manager.load_config()
                    api_manager.save_config(config)
                    api_manager.switch_config(config_name.strip())
                    
                    success, msg = api_manager.test_connection()
                    
                    if original_config:
                        api_manager.switch_config(original_config.name)
                    
                    if success:
                        display_success(msg)
                    else:
                        display_error(msg)
                except Exception as e:
                    display_error("测试连接时发生错误", str(e))
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_prompt_settings_card():
    """渲染提示词管理卡片"""
    api_manager = st.session_state.api_manager
    
    if api_manager is None:
        display_error("API 管理器未初始化")
        return
    
    from src.prompts import PromptManager
    PromptManager.set_api_manager(api_manager)
    
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">提示词管理</div>', unsafe_allow_html=True)
    
    st.caption("修改提示词可以调整脚本生成的风格和输出格式")
    
    prompt_types = {
        "draft": "脚本生成",
        "review": "脚本评审", 
        "refine": "脚本修正"
    }
    
    selected_type = st.selectbox(
        "选择提示词类型",
        list(prompt_types.keys()),
        format_func=lambda x: prompt_types[x],
        key="settings_prompt_type"
    )
    
    custom_prompt = api_manager.get_prompt(selected_type)
    default_prompt = PromptManager.get_default_template(selected_type)
    
    current_prompt = custom_prompt if custom_prompt else default_prompt
    is_custom = custom_prompt is not None
    
    if is_custom:
        st.info("当前使用自定义提示词")
    else:
        st.info("当前使用默认提示词")
    
    st.markdown("#### 提示词内容")
    st.caption("可用变量: {game_intro}, {usp}, {target_audience}, {category}, {references}, {script}, {review_feedback}")
    
    edited_prompt = st.text_area(
        "编辑提示词",
        value=current_prompt,
        height=400,
        key=f"settings_prompt_editor_{selected_type}",
        label_visibility="collapsed"
    )
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col2:
        if st.button("复制默认", use_container_width=True, key=f"settings_copy_default_{selected_type}", type="secondary"):
            st.session_state[f"settings_prompt_editor_{selected_type}"] = default_prompt
            st.rerun()
    
    with col3:
        if st.button("重置", use_container_width=True, key=f"settings_reset_prompt_{selected_type}", type="secondary"):
            success, msg = api_manager.reset_prompt(selected_type)
            if success:
                display_success("已重置为默认提示词")
                st.rerun()
            else:
                display_error(f"重置失败: {msg}")
    
    with col4:
        if st.button("保存", use_container_width=True, key=f"settings_save_prompt_{selected_type}", type="primary"):
            if edited_prompt.strip():
                success, msg = api_manager.save_prompt(selected_type, edited_prompt)
                if success:
                    display_success("提示词已保存")
                    st.rerun()
                else:
                    display_error(f"保存失败: {msg}")
            else:
                display_error("提示词内容不能为空")
    
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 主程序入口 ====================
def main():
    """主程序入口"""
    inject_custom_css()
    
    is_healthy, errors = check_system_health()
    
    if not is_healthy:
        st.markdown("# CreativElixir")
        st.markdown("---")
        st.markdown("### 系统初始化错误")
        for error in errors:
            display_error(error)
        st.markdown("---")
        st.markdown("请检查以下内容：")
        st.markdown("1. 确保 `./data` 目录存在且有写入权限")
        st.markdown("2. 检查依赖是否正确安装")
        st.markdown("3. 重启应用后重试")
        return
    
    selected_page = render_navigation()
    
    if selected_page == "脚本生成":
        render_script_generation_page()
    elif selected_page == "知识库":
        render_knowledge_base_page()
    elif selected_page == "项目历史":
        render_project_history_page()
    elif selected_page == "设置":
        render_settings_page()


if __name__ == "__main__":
    main()
