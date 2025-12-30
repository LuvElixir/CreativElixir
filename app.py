"""
游戏信息流广告脚本自动化工具 - 主应用入口

基于 Streamlit 构建的 AI 驱动广告脚本生成工具。
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
    page_title="游戏广告脚本生成器",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== CSS 注入模块 ====================
def inject_custom_css():
    """
    注入自定义 CSS 样式
    
    实现 SaaS 风格的深色科技感主题，包括：
    - 隐藏 Streamlit 默认元素（汉堡菜单、Footer）
    - 卡片容器样式
    - 输入组件圆角样式
    - 按钮样式优化
    - 徽章组件样式
    - 时间线组件样式
    - 信息层级样式
    - 响应式断点样式
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 5.4, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3
    """
    st.markdown("""
    <style>
    /* 隐藏 Streamlit 默认元素（保留 header 以便打开侧边栏） */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* 不隐藏 header，保留侧边栏切换按钮 */
    
    /* 主应用背景 */
    .stApp {
        background-color: #111827;
    }
    
    /* 卡片容器样式 - 旧版兼容 */
    .st-card {
        background-color: #1f2937;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #374151;
        margin-bottom: 16px;
    }
    
    /* ==================== 卡片组件样式 ==================== */
    /* Requirements: 2.1, 7.3 */
    .ui-card {
        background-color: #1f2937;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #374151;
        margin-bottom: 16px;
        min-width: 300px;
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
    /* Requirements: 8.3 */
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
    /* Requirements: 5.4 */
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
    /* Requirements: 8.1, 8.2 */
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
    
    /* ==================== 页面头部样式 ==================== */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-bottom: 16px;
        border-bottom: 1px solid #374151;
    }
    
    .page-header-info {
        display: flex;
        gap: 16px;
        align-items: center;
    }
    
    /* ==================== 响应式断点样式 ==================== */
    /* Requirements: 7.1, 7.2, 7.4 */
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
    /* Requirements: 7.4 */
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
    </style>
    """, unsafe_allow_html=True)


# ==================== UI 辅助函数 ====================
def render_badge(text: str, variant: str = "primary") -> str:
    """
    渲染徽章组件
    
    生成带有指定样式的徽章 HTML 字符串，用于显示品类标签、状态信息等。
    
    Args:
        text: 徽章显示的文本内容
        variant: 样式变体，可选值:
            - "primary": 主要样式（紫色背景）
            - "secondary": 次要样式（灰色背景）
            - "success": 成功样式（绿色背景）
    
    Returns:
        str: 徽章的 HTML 字符串
        
    Requirements: 8.3
    
    Example:
        >>> badge_html = render_badge("SLG", "primary")
        >>> st.markdown(badge_html, unsafe_allow_html=True)
    """
    return f'<span class="ui-badge ui-badge-{variant}">{text}</span>'


def render_page_header():
    """
    渲染页面头部状态信息
    
    在页面顶部显示当前项目状态和模型配置信息，包括：
    - 项目名称和客户名称
    - 生成模型信息
    - 评审模型信息（如果配置了独立的评审模型）
    
    未选择项目时显示"未选择项目"提示。
    使用紧凑的单行布局展示所有状态信息。
    
    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    # 获取当前状态
    project = st.session_state.get("current_project")
    api_manager = st.session_state.get("api_manager")
    gen_config = api_manager.load_config() if api_manager else None
    rev_manager = st.session_state.get("review_api_manager")
    
    # 构建头部信息
    header_parts = []
    
    # 项目信息
    if project:
        header_parts.append(f"**项目:** {project.client_name} / {project.project_name}")
    else:
        header_parts.append("**项目:** 未选择项目")
    
    # 模型信息
    if gen_config:
        model_info = f"**生成:** {gen_config.model_id}"
        if rev_manager:
            rev_config = rev_manager.load_config()
            if rev_config:
                model_info += f" | **评审:** {rev_config.model_id}"
        header_parts.append(model_info)
    
    # 使用单行紧凑布局显示
    st.markdown(" · ".join(header_parts))


# ==================== 导航组件 ====================
def render_navigation() -> str:
    """
    渲染侧边栏导航菜单
    
    使用 streamlit-option-menu 创建导航菜单，配置深色主题样式。
    
    Returns:
        str: 选中的菜单项名称
        
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """
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
    """
    显示用户友好的错误信息
    
    Args:
        message: 主要错误信息
        details: 可选的详细信息
    """
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


def safe_operation(operation_name: str):
    """
    安全操作装饰器，用于捕获和处理异常
    
    Args:
        operation_name: 操作名称，用于错误提示
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                display_error(f"{operation_name}失败: {str(e)}")
                return None
            except IOError as e:
                display_error(f"{operation_name}时发生文件操作错误", str(e))
                return None
            except Exception as e:
                display_error(
                    f"{operation_name}时发生未知错误",
                    f"错误类型: {type(e).__name__}\n错误信息: {str(e)}\n\n{traceback.format_exc()}"
                )
                return None
        return wrapper
    return decorator


def validate_api_config(api_manager: APIManager) -> Tuple[bool, str]:
    """
    验证 API 配置是否有效
    
    Args:
        api_manager: API 管理器实例
        
    Returns:
        (是否有效, 错误信息)
    """
    config = api_manager.load_config()
    if not config:
        return False, "未配置 API，请先在侧边栏配置 API 设置"
    
    is_valid, error_msg = config.is_valid()
    if not is_valid:
        return False, f"API 配置无效: {error_msg}"
    
    return True, ""


def validate_generation_input(game_intro: str, usp: str, target_audience: str, category: str) -> Tuple[bool, str]:
    """
    验证脚本生成输入
    
    Args:
        game_intro: 游戏介绍
        usp: 独特卖点
        target_audience: 目标人群
        category: 游戏品类
        
    Returns:
        (是否有效, 错误信息)
    """
    errors = []
    
    if not game_intro or not game_intro.strip():
        errors.append("游戏介绍不能为空")
    if not usp or not usp.strip():
        errors.append("独特卖点 (USP) 不能为空")
    if not target_audience or not target_audience.strip():
        errors.append("目标人群不能为空")
    if not category or not category.strip():
        errors.append("请选择游戏品类")
    
    if errors:
        return False, "、".join(errors)
    
    return True, ""

# 初始化 session state
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
            # 传递 API 管理器给 RAG 系统，以便调用 embedding 模型
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
    
    # 设置 PromptManager 的 API 管理器引用
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
    # 评审模型相关 session state
    # Requirements: 5.1, 5.2, 5.3
    if "review_api_manager" not in st.session_state:
        st.session_state.review_api_manager = None
    if "selected_review_config" not in st.session_state:
        st.session_state.selected_review_config = "使用生成模型"


def check_system_health() -> Tuple[bool, list]:
    """
    检查系统各模块健康状态
    
    Returns:
        (是否健康, 错误列表)
    """
    errors = []
    
    if st.session_state.api_manager is None:
        errors.append(f"API 管理器初始化失败: {st.session_state.get('init_error_api', '未知错误')}")
    
    if st.session_state.rag_system is None:
        errors.append(f"知识库系统初始化失败: {st.session_state.get('init_error_rag', '未知错误')}")
    
    if st.session_state.project_manager is None:
        errors.append(f"项目管理器初始化失败: {st.session_state.get('init_error_project', '未知错误')}")
    
    return len(errors) == 0, errors


init_session_state()


# ==================== 侧边栏 ====================
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # Logo 和标题
        st.markdown("# 游戏广告脚本生成器")
        st.markdown("---")
        
        # API 设置
        render_api_settings()
        
        st.markdown("---")
        
        # 提示词管理
        render_prompt_management()
        
        st.markdown("---")
        
        # 项目管理
        render_project_management()
        
        st.markdown("---")
        
        # 知识库管理
        render_knowledge_base_management()


def render_review_model_settings():
    """渲染评审模型设置区域（独立显示）"""
    with st.expander("🎯 评审模型设置", expanded=True):
        api_manager = st.session_state.api_manager
        
        if api_manager is None:
            display_warning("请先配置 API")
            return
        
        try:
            all_configs = api_manager.get_all_configs()
        except Exception as e:
            display_error("加载 API 配置失败", str(e))
            return
        
        if not all_configs:
            display_warning("请先在 API 设置中添加配置")
            return
        
        config_names = [config.name for config in all_configs]
        
        st.caption("选择用于脚本评审的模型，可以与生成模型不同以获得多元视角")
        
        # 默认选项：使用生成模型
        review_options = ["使用生成模型"] + config_names
        
        # 获取当前选中的评审模型
        current_review_selection = st.session_state.get("selected_review_config", "使用生成模型")
        if current_review_selection not in review_options:
            current_review_selection = "使用生成模型"
        
        selected_review_model = st.selectbox(
            "评审模型",
            review_options,
            index=review_options.index(current_review_selection),
            help="选择用于脚本评审的模型",
            key="review_model_select_main"
        )
        
        # 保存到 session_state
        if selected_review_model == "使用生成模型":
            st.session_state.review_api_manager = None
            st.session_state.selected_review_config = "使用生成模型"
            st.info("评审将使用与生成相同的模型")
        else:
            # 创建评审专用的 API 管理器
            try:
                review_api_manager = APIManager()
                review_api_manager.switch_config(selected_review_model)
                st.session_state.review_api_manager = review_api_manager
                st.session_state.selected_review_config = selected_review_model
                
                # 显示当前配置
                rev_config = review_api_manager.load_config()
                if rev_config:
                    st.success(f"评审模型: {rev_config.model_id}")
            except Exception as e:
                display_warning(f"评审模型配置加载失败: {str(e)}")
                st.session_state.review_api_manager = None
                st.session_state.selected_review_config = "使用生成模型"


def render_api_settings():
    """渲染 API 设置区域"""
    with st.expander("API 设置", expanded=False):
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
        
        # 配置选择区域
        if all_configs:
            st.markdown("#### 选择配置")
            config_names = [config.name for config in all_configs]
            
            # 确保当前活动配置在列表中
            if active_config_name not in config_names and config_names:
                active_config_name = config_names[0]
            
            selected_config_name = st.selectbox(
                "当前使用的配置",
                config_names,
                index=config_names.index(active_config_name) if active_config_name in config_names else 0,
                help="选择要使用的 API 配置"
            )
            
            # 切换配置
            if selected_config_name != active_config_name:
                try:
                    success, msg = api_manager.switch_config(selected_config_name)
                    if success:
                        # 更新 RAG 系统的 API 管理器
                        if st.session_state.rag_system:
                            st.session_state.rag_system.update_api_manager(api_manager)
                        display_success(f"已切换到配置: {selected_config_name}")
                        st.rerun()
                    else:
                        display_error(f"切换失败: {msg}")
                except Exception as e:
                    display_error("切换配置时发生错误", str(e))
            
            # 显示当前配置信息
            if current_config:
                config_info = f"当前配置: {current_config.name} ({current_config.model_id})"
                if current_config.has_embedding_config():
                    config_info += f"\nEmbedding: {current_config.embedding_model}"
                st.info(config_info)
            
            st.markdown("---")
            
            # 删除配置按钮
            if len(all_configs) > 1:  # 至少保留一个配置
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("删除", key="delete_config", type="secondary"):
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
        
        st.markdown("---")
        st.markdown("#### 添加/编辑配置")
        
        # 配置表单
        with st.form("api_config_form"):
            # 如果选择了现有配置，预填充表单
            edit_config = None
            if all_configs and current_config:
                edit_config = current_config
            
            config_name = st.text_input(
                "配置名称",
                value=edit_config.name if edit_config else "",
                help="为此配置起一个名称，方便管理多个 API 配置"
            )
            api_key = st.text_input(
                "API Key",
                value=edit_config.api_key if edit_config else "",
                type="password",
                help="您的 API 密钥，支持 OpenAI 及兼容格式的 API"
            )
            base_url = st.text_input(
                "Base URL",
                value=edit_config.base_url if edit_config else "https://api.openai.com/v1",
                help="API 服务地址，如 OpenAI、文心一言、豆包等"
            )
            model_id = st.text_input(
                "Model ID",
                value=edit_config.model_id if edit_config else "gpt-4",
                help="模型标识符，如 gpt-4、gpt-3.5-turbo 等"
            )
            
            # Embedding 模型配置
            st.markdown("---")
            st.markdown("##### Embedding 模型 (知识库向量检索)")
            
            from src.api_manager import EMBEDDING_MODELS
            
            # 获取当前配置的 embedding 信息
            current_embedding_provider = ""
            current_embedding_model = ""
            if edit_config and edit_config.embedding_model:
                # 根据 embedding_base_url 判断当前 provider
                emb_url = edit_config.embedding_base_url or ""
                if "volces.com" in emb_url or "ark" in emb_url:
                    current_embedding_provider = "doubao"
                elif "siliconflow" in emb_url:
                    current_embedding_provider = "siliconflow"
                else:
                    current_embedding_provider = "openai"
                current_embedding_model = edit_config.embedding_model
            
            # Embedding 提供商选择
            embedding_providers = ["不使用"] + list(EMBEDDING_MODELS.keys())
            provider_names = ["不使用"] + [EMBEDDING_MODELS[k]["name"] for k in EMBEDDING_MODELS.keys()]
            
            # 找到当前 provider 的索引
            provider_idx = 0
            if current_embedding_provider in embedding_providers:
                provider_idx = embedding_providers.index(current_embedding_provider)
            
            selected_provider_name = st.selectbox(
                "Embedding 提供商",
                provider_names,
                index=provider_idx,
                help="选择 Embedding 模型提供商，用于知识库向量检索"
            )
            
            # 获取选中的 provider key
            selected_provider = ""
            if selected_provider_name != "不使用":
                for k, v in EMBEDDING_MODELS.items():
                    if v["name"] == selected_provider_name:
                        selected_provider = k
                        break
            
            # Embedding 模型选择
            embedding_model = ""
            embedding_base_url = ""
            
            if selected_provider and selected_provider in EMBEDDING_MODELS:
                provider_info = EMBEDDING_MODELS[selected_provider]
                model_options = provider_info["models"]
                model_names = [m["name"] for m in model_options]
                model_ids = [m["id"] for m in model_options]
                
                # 找到当前模型的索引
                model_idx = 0
                if current_embedding_model in model_ids:
                    model_idx = model_ids.index(current_embedding_model)
                
                selected_model_name = st.selectbox(
                    "Embedding 模型",
                    model_names,
                    index=model_idx,
                    help="选择具体的 Embedding 模型"
                )
                
                # 获取选中的模型 ID
                for m in model_options:
                    if m["name"] == selected_model_name:
                        embedding_model = m["id"]
                        break
                
                embedding_base_url = provider_info["base_url"]
                
                st.caption(f"API 地址: {embedding_base_url}")
                
                # Embedding API Key（如果与 LLM 提供商不同，需要单独填写）
                embedding_api_key = st.text_input(
                    "Embedding API Key",
                    value=edit_config.embedding_api_key if edit_config else "",
                    type="password",
                    help="如果 Embedding 提供商与 LLM 不同，请填写对应的 API Key。留空则使用上方的 API Key"
                )
            else:
                embedding_api_key = ""
            
            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("保存配置", use_container_width=True)
            with col2:
                test_btn = st.form_submit_button("测试连接", use_container_width=True)
        
        if save_btn:
            # 验证输入
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
                        # 自动切换到新保存的配置
                        api_manager.switch_config(config_name.strip())
                        # 更新 RAG 系统的 API 管理器
                        if st.session_state.rag_system:
                            st.session_state.rag_system.update_api_manager(api_manager)
                        display_success("配置保存成功并已激活！")
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
                        # 临时保存配置用于测试
                        config = APIConfig(
                            api_key=api_key.strip(),
                            base_url=base_url.strip(),
                            model_id=model_id.strip(),
                            name=config_name.strip()
                        )
                        # 临时切换配置进行测试
                        original_config = api_manager.load_config()
                        api_manager.save_config(config)
                        api_manager.switch_config(config_name.strip())
                        
                        success, msg = api_manager.test_connection()
                        
                        # 恢复原配置
                        if original_config:
                            api_manager.switch_config(original_config.name)
                        
                        if success:
                            display_success(msg)
                        else:
                            display_error(msg)
                    except Exception as e:
                        display_error("测试连接时发生错误", str(e))


def render_prompt_management():
    """渲染提示词管理区域"""
    with st.expander("提示词管理", expanded=False):
        api_manager = st.session_state.api_manager
        
        if api_manager is None:
            display_error("API 管理器未初始化")
            return
        
        from src.prompts import PromptManager
        
        # 设置 API 管理器引用
        PromptManager.set_api_manager(api_manager)
        
        st.markdown("#### 自定义提示词")
        st.caption("修改提示词可以调整脚本生成的风格和输出格式")
        
        # 提示词类型选择
        prompt_types = {
            "draft": "脚本生成",
            "review": "脚本评审", 
            "refine": "脚本修正"
        }
        
        selected_type = st.selectbox(
            "选择提示词类型",
            list(prompt_types.keys()),
            format_func=lambda x: prompt_types[x],
            help="选择要编辑的提示词类型"
        )
        
        # 获取当前提示词（自定义或默认）
        custom_prompt = api_manager.get_prompt(selected_type)
        default_prompt = PromptManager.get_default_template(selected_type)
        
        current_prompt = custom_prompt if custom_prompt else default_prompt
        is_custom = custom_prompt is not None
        
        # 显示状态
        if is_custom:
            st.info("当前使用自定义提示词")
        else:
            st.info("当前使用默认提示词")
        
        # 提示词编辑区
        st.markdown("##### 提示词内容")
        st.caption("可用变量: {game_intro}, {usp}, {target_audience}, {category}, {references}, {script}, {review_feedback}")
        
        edited_prompt = st.text_area(
            "编辑提示词",
            value=current_prompt,
            height=400,
            key=f"prompt_editor_{selected_type}",
            label_visibility="collapsed"
        )
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("保存", use_container_width=True, key=f"save_prompt_{selected_type}", type="primary"):
                if edited_prompt.strip():
                    success, msg = api_manager.save_prompt(selected_type, edited_prompt)
                    if success:
                        display_success("提示词已保存")
                        st.rerun()
                    else:
                        display_error(f"保存失败: {msg}")
                else:
                    display_error("提示词内容不能为空")
        
        with col2:
            if st.button("重置", use_container_width=True, key=f"reset_prompt_{selected_type}", type="secondary"):
                success, msg = api_manager.reset_prompt(selected_type)
                if success:
                    display_success("已重置为默认提示词")
                    st.rerun()
                else:
                    display_error(f"重置失败: {msg}")
        
        with col3:
            if st.button("复制默认", use_container_width=True, key=f"copy_default_{selected_type}", type="secondary"):
                st.session_state[f"prompt_editor_{selected_type}"] = default_prompt
                st.rerun()


def render_project_management():
    """渲染项目管理区域"""
    with st.expander("项目管理", expanded=False):
        project_manager = st.session_state.project_manager
        
        if project_manager is None:
            display_error("项目管理器未初始化", st.session_state.get('init_error_project'))
            return
        
        # 创建新项目
        st.markdown("#### 创建新项目")
        with st.form("create_project_form"):
            new_client = st.text_input("客户名称", help="客户或公司名称")
            new_project = st.text_input("项目名称", help="项目或游戏名称")
            create_btn = st.form_submit_button("创建项目", use_container_width=True)
        
        if create_btn:
            if not new_client or not new_client.strip():
                display_error("请填写客户名称")
            elif not new_project or not new_project.strip():
                display_error("请填写项目名称")
            else:
                try:
                    project = project_manager.create_project(new_client.strip(), new_project.strip())
                    st.session_state.current_project = project
                    display_success(f"项目 '{new_client}/{new_project}' 创建成功！")
                    st.rerun()
                except ValueError as e:
                    display_error(str(e))
                except Exception as e:
                    display_error("创建项目时发生错误", str(e))
        
        st.markdown("---")
        
        # 选择现有项目
        st.markdown("#### 选择项目")
        try:
            clients = project_manager.list_clients()
        except Exception as e:
            display_error("获取客户列表失败", str(e))
            clients = []
        
        if clients:
            selected_client = st.selectbox("选择客户", [""] + clients)
            
            if selected_client:
                try:
                    projects = project_manager.get_projects_by_client(selected_client)
                    project_names = [p.project_name for p in projects]
                except Exception as e:
                    display_error("获取项目列表失败", str(e))
                    project_names = []
                
                if project_names:
                    selected_project = st.selectbox("选择项目", [""] + project_names)
                    
                    if selected_project:
                        try:
                            project = project_manager.get_project(selected_client, selected_project)
                        except Exception as e:
                            display_error("加载项目失败", str(e))
                            project = None
                        
                        if project:
                            if st.button("加载项目", use_container_width=True, type="primary"):
                                st.session_state.current_project = project
                                display_success(f"已加载项目: {selected_client}/{selected_project}")
                                st.rerun()
                            
                            if st.button("删除项目", use_container_width=True, type="secondary"):
                                try:
                                    if project_manager.delete_project(selected_client, selected_project):
                                        if (st.session_state.current_project and 
                                            st.session_state.current_project.client_name == selected_client and
                                            st.session_state.current_project.project_name == selected_project):
                                            st.session_state.current_project = None
                                        display_success("项目已删除")
                                        st.rerun()
                                    else:
                                        display_error("删除失败，请稍后重试")
                                except Exception as e:
                                    display_error("删除项目时发生错误", str(e))
        else:
            display_info("暂无项目，请先创建")
        
        # 显示当前项目
        if st.session_state.current_project:
            st.markdown("---")
            st.markdown("#### 当前项目")
            current = st.session_state.current_project
            st.info(f"当前项目: {current.client_name} / {current.project_name}")


def render_knowledge_base_management():
    """渲染知识库管理区域"""
    with st.expander("知识库管理", expanded=False):
        rag_system = st.session_state.rag_system
        
        if rag_system is None:
            display_error("知识库系统未初始化", st.session_state.get('init_error_rag'))
            return
        
        # 显示知识库状态
        try:
            total_scripts = rag_system.get_script_count()
            categories = rag_system.get_categories()
            
            st.metric("脚本总数", total_scripts)
            st.caption(f"品类: {', '.join(categories)}")
            
            # 显示 向量数据库 状态
            if rag_system.is_vector_db_available():
                # 检查是否有 API 配置用于 embedding
                api_config = rag_system._api_manager.load_config() if rag_system._api_manager else None
                if api_config and api_config.has_embedding_config():
                    # 显示当前使用的 embedding 模型
                    emb_url = api_config.embedding_base_url or ""
                    if "volces.com" in emb_url or "ark" in emb_url:
                        provider_name = "豆包"
                    elif "siliconflow" in emb_url:
                        provider_name = "硅基流动"
                    else:
                        provider_name = "OpenAI"
                    st.caption(f"向量检索已启用 ({provider_name}: {api_config.embedding_model})")
                else:
                    st.caption("向量数据库已安装，请配置 Embedding 模型")
            else:
                st.caption("向量数据库未安装")
        except Exception as e:
            display_error("获取知识库状态失败", str(e))
        
        st.markdown("---")
        
        # 导出知识库
        st.markdown("#### 导出知识库")
        if st.button("导出为 ZIP", use_container_width=True, type="secondary"):
            with st.spinner("正在导出..."):
                try:
                    export_path = "./data/knowledge_base_export"
                    success, result = rag_system.export_knowledge_base(export_path)
                    if success:
                        # 提供下载
                        try:
                            with open(result, "rb") as f:
                                st.download_button(
                                    label="下载导出文件",
                                    data=f,
                                    file_name="knowledge_base.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            display_success("导出成功！")
                        except Exception as e:
                            display_error("读取导出文件失败", str(e))
                    else:
                        display_error(result)
                except Exception as e:
                    display_error("导出知识库时发生错误", str(e))
        
        st.markdown("---")
        
        # 导入知识库
        st.markdown("#### 导入知识库")
        uploaded_file = st.file_uploader(
            "上传知识库 ZIP 文件",
            type=["zip"],
            key="kb_import",
            help="上传之前导出的知识库 ZIP 文件"
        )
        
        if uploaded_file:
            if st.button("导入知识库", use_container_width=True, type="primary"):
                with st.spinner("正在导入..."):
                    try:
                        # 保存上传的文件
                        import_path = Path("./data/_temp_import.zip")
                        import_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(import_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        # 导入
                        success, msg = rag_system.import_knowledge_base(str(import_path))
                        
                        # 清理临时文件
                        if import_path.exists():
                            import_path.unlink()
                        
                        if success:
                            display_success(msg)
                            st.rerun()
                        else:
                            display_error(msg)
                    except Exception as e:
                        display_error("导入知识库时发生错误", str(e))
                        # 清理临时文件
                        import_path = Path("./data/_temp_import.zip")
                        if import_path.exists():
                            import_path.unlink()


# ==================== 主界面 ====================
def render_main_content():
    """渲染主界面内容"""
    # 显示当前项目信息
    if st.session_state.current_project:
        current = st.session_state.current_project
        st.markdown(f"**当前项目:** {current.client_name} / {current.project_name}")
    
    # 主界面标签页
    tabs = st.tabs(["脚本生成", "知识库", "项目历史"])
    
    with tabs[0]:
        render_script_generation_tab()
    
    with tabs[1]:
        render_knowledge_base_tab()
    
    with tabs[2]:
        render_project_history_tab()


def render_script_generation_tab():
    """
    渲染脚本生成标签页
    
    使用卡片布局组织输入区域：
    - 项目信息卡片：项目名称、客户名称、品类
    - 脚本参数卡片：游戏介绍、USP、目标人群（3:1 列比例）
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5
    """
    st.markdown("### 脚本生成")
    
    # 检查系统健康状态
    is_healthy, errors = check_system_health()
    if not is_healthy:
        for error in errors:
            display_error(error)
        return
    
    # 检查 API 配置
    api_manager = st.session_state.api_manager
    is_valid, error_msg = validate_api_config(api_manager)
    if not is_valid:
        display_warning(error_msg)
        return
    
    # ==================== 页面头部 ====================
    # Requirements: 1.1, 1.2, 1.3, 1.4
    render_page_header()
    
    # 获取品类列表
    try:
        categories = st.session_state.rag_system.get_categories()
    except Exception:
        categories = ["SLG", "MMO", "休闲", "卡牌", "二次元", "模拟经营"]
    
    default_category = st.session_state.current_project.category if st.session_state.current_project else ""
    default_idx = categories.index(default_category) if default_category in categories else 0
    
    # ==================== 项目信息卡片 ====================
    # Requirements: 2.1, 2.2
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">项目信息</div>', unsafe_allow_html=True)
    
    # 项目名称、客户名称、品类 (3列)
    proj_col1, proj_col2, proj_col3 = st.columns([2, 2, 1])
    with proj_col1:
        project_name = st.text_input(
            "项目/游戏名称",
            value=st.session_state.current_project.project_name if st.session_state.current_project else "",
            placeholder="请输入项目或游戏名称...",
            help="当前项目或游戏名称"
        )
    with proj_col2:
        client_name = st.text_input(
            "客户名称",
            value=st.session_state.current_project.client_name if st.session_state.current_project else "",
            placeholder="请输入客户名称...",
            help="客户或公司名称，用于项目归档"
        )
    with proj_col3:
        category = st.selectbox(
            "游戏品类",
            categories,
            index=default_idx,
            help="选择游戏所属品类，用于检索同品类参考脚本"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== 脚本参数卡片 ====================
    # Requirements: 2.3, 2.4
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">脚本参数</div>', unsafe_allow_html=True)
    
    # 使用 3:1 列比例布局游戏介绍和其他输入
    param_col1, param_col2 = st.columns([3, 1])
    
    with param_col1:
        game_intro = st.text_area(
            "游戏介绍",
            height=150,
            placeholder="请输入游戏的基本介绍，包括游戏类型、玩法特点等...",
            value=st.session_state.current_project.game_intro if st.session_state.current_project else "",
            help="详细描述游戏的核心玩法和特色"
        )
    
    with param_col2:
        usp = st.text_area(
            "独特卖点 (USP)",
            height=70,
            placeholder="请输入游戏的独特卖点...",
            value=st.session_state.current_project.usp if st.session_state.current_project else "",
            help="游戏区别于竞品的核心优势"
        )
        target_audience = st.text_area(
            "目标人群",
            height=70,
            placeholder="请描述目标用户群体...",
            value=st.session_state.current_project.target_audience if st.session_state.current_project else "",
            help="广告投放的目标受众特征"
        )
    
    # 评审模型选择（放在脚本参数卡片内）
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
                help="选择评审模型，可与生成模型不同",
                key="review_model_main"
            )
        
        # 保存到 session_state
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
        # 验证输入
        is_valid, error_msg = validate_generation_input(game_intro, usp, target_audience, category)
        if not is_valid:
            display_error(error_msg)
            return
        
        # 验证项目名称和客户名称
        if not project_name or not project_name.strip():
            display_error("请输入项目/游戏名称")
            return
        if not client_name or not client_name.strip():
            display_error("请输入客户名称")
            return
        
        # 自动保存/更新项目信息到历史记录
        try:
            project_manager = st.session_state.project_manager
            
            # 检查项目是否已存在
            existing_project = project_manager.get_project(client_name.strip(), project_name.strip())
            
            if existing_project:
                # 更新现有项目
                existing_project.game_intro = game_intro
                existing_project.usp = usp
                existing_project.target_audience = target_audience
                existing_project.category = category
                project_manager.update_project(existing_project)
                st.session_state.current_project = existing_project
            else:
                # 创建新项目
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
        
        # 创建生成输入
        input_data = GenerationInput(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category
        )
        
        # 创建生成器
        # Requirements: 5.4, 5.6
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
        # Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        with st.status("正在构建创意...", expanded=True) as status:
            full_output = ""
            
            try:
                # RAG 检索阶段
                status.write("正在检索同品类参考脚本...")
                
                # 初稿生成阶段
                status.write("正在生成脚本初稿...")
                
                gen = generator.generate(input_data)
                for chunk in gen:
                    full_output += chunk
                
                # 评审阶段
                status.write("正在评审脚本质量...")
                
                # 修正阶段
                status.write("正在优化脚本...")
                
                # 获取最终输出
                try:
                    output = gen.send(None)
                except StopIteration as e:
                    output = e.value
                
                st.session_state.generated_script = full_output
                st.session_state.generation_output = output
                st.session_state.last_error = None
                
                # 完成 - 收起状态容器
                status.update(label="创意构建完成!", state="complete", expanded=False)
                
            except Exception as e:
                st.session_state.last_error = str(e)
                status.update(label="生成失败", state="error", expanded=True)
                display_error("脚本生成失败", str(e))
    
    # ==================== 结果展示区域 ====================
    # Requirements: 3.1, 3.2, 3.3, 3.4
    if st.session_state.generation_output:
        st.markdown("---")
        
        output = st.session_state.generation_output
        
        # 使用卡片包裹结果表格
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="ui-card-header">生成结果</div>', unsafe_allow_html=True)
        
        if output.is_valid():
            # 结果摘要（分镜数量）
            # Requirements: 3.2
            storyboard_count = len(output.storyboard)
            st.markdown(f"已生成 **{storyboard_count}** 个分镜")
            
            # 构建 DataFrame 用于 st.data_editor
            max_len = max(
                len(output.storyboard),
                len(output.voiceover),
                len(output.design_intent)
            )
            
            # 填充列表使其长度一致
            storyboard_padded = output.storyboard + [""] * (max_len - len(output.storyboard))
            voiceover_padded = output.voiceover + [""] * (max_len - len(output.voiceover))
            design_intent_padded = output.design_intent + [""] * (max_len - len(output.design_intent))
            
            df = pd.DataFrame({
                "分镜": storyboard_padded,
                "口播": voiceover_padded,
                "设计意图": design_intent_padded
            })
            
            # 可编辑表格
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
            
            # 操作按钮 - 右对齐
            # Requirements: 3.3
            btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])
            with btn_col2:
                if st.button("导出", use_container_width=True, type="secondary"):
                    # 导出为 CSV
                    try:
                        csv_data = edited_df.to_csv(index=False).encode('utf-8-sig')
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
                        # 确定品类
                        archive_category = category if 'category' in dir() else (
                            st.session_state.current_project.category if st.session_state.current_project else "SLG"
                        )
                        
                        # 从编辑后的 DataFrame 获取数据
                        edited_storyboard = edited_df["分镜"].tolist()
                        edited_voiceover = edited_df["口播"].tolist()
                        edited_design_intent = edited_df["设计意图"].tolist()
                        
                        # 过滤空行
                        edited_storyboard = [s for s in edited_storyboard if s.strip()]
                        edited_voiceover = [v for v in edited_voiceover if v.strip()]
                        edited_design_intent = [d for d in edited_design_intent if d.strip()]
                        
                        # 添加到知识库
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
                        
                        # 添加到项目历史
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
            # 显示原始内容
            st.markdown("**原始输出:**")
            st.text(output.raw_content)
            display_warning("脚本格式解析失败，显示原始内容。您可以手动复制并编辑。")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_quick_capture_panel():
    """
    渲染快速采集面板
    
    提供纯文本粘贴入口和 AI 分析功能，实现：
    - 展开的 expander 容器，标题为 "🚀 快速采集 (AI 智能打标)"
    - text_area 用于粘贴广告文案
    - "AI 分析并入库" 主按钮
    - 点击后显示 spinner 和结果展示
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
    """
    rag_system = st.session_state.rag_system
    
    with st.expander("🚀 快速采集 (AI 智能打标)", expanded=True):
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
                            # 显示成功消息，包含归档品类
                            category = metadata.category if metadata else "其他"
                            display_success(f"✅ 入库成功！已归档至品类: {category}")
                            
                            # 显示提取的元数据 JSON
                            if metadata:
                                st.markdown("**提取的元数据:**")
                                import json
                                metadata_json = json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2)
                                st.code(metadata_json, language="json")
                        else:
                            # 显示错误信息
                            display_error(f"入库失败: {message}")
                    except Exception as e:
                        display_error(f"处理异常: {str(e)}")


def render_knowledge_base_tab():
    """
    渲染知识库标签页
    
    优化布局：
    - 快速采集面板（顶部，展开状态）
    - 统计卡片区域（脚本总数、品类数量）
    - 筛选栏固定在列表上方
    - 脚本列表使用卡片样式
    - 每个脚本卡片显示品类徽章、游戏名称、入库时间
    - 支持展开/收起查看详情
    - 批量导入工具（底部，折叠状态）
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4
    """
    st.markdown("### 知识库浏览")
    
    # ==================== 快速采集面板（顶部） ====================
    # Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.3, 5.4
    render_quick_capture_panel()
    
    st.markdown("---")
    
    rag_system = st.session_state.rag_system
    
    if rag_system is None:
        display_error("知识库系统未初始化")
        return
    
    try:
        categories = rag_system.get_categories()
    except Exception as e:
        display_error("获取品类列表失败", str(e))
        categories = []
    
    # 获取所有脚本用于统计
    try:
        all_scripts = []
        for cat in categories:
            all_scripts.extend(rag_system.get_scripts_by_category(cat))
        total_script_count = len(all_scripts)
    except Exception as e:
        display_error("获取脚本统计失败", str(e))
        total_script_count = 0
    
    # ==================== 统计卡片区域 ====================
    # Requirements: 4.1
    stat_col1, stat_col2, stat_col3 = st.columns([1, 1, 2])
    
    with stat_col1:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.metric("脚本总数", total_script_count)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.metric("品类数量", len(categories))
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== 筛选栏 ====================
    # Requirements: 4.2
    with stat_col3:
        selected_category = st.selectbox(
            "筛选品类", 
            ["全部"] + categories, 
            key="kb_category_filter",
            help="选择品类筛选脚本列表"
        )
    
    st.markdown("---")
    
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
    # Requirements: 4.3, 4.4, 4.5
    if scripts:
        for i, script in enumerate(scripts):
            render_script_card(script, i, rag_system)
    else:
        display_info("暂无脚本数据")
    
    st.markdown("---")
    
    # ==================== 数据管理区域 ====================
    st.markdown("#### 数据管理")
    
    # 导出按钮（保持可见）
    if st.button("导出知识库", use_container_width=False, type="secondary"):
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
                            use_container_width=False
                        )
                else:
                    display_error(result)
            except Exception as e:
                display_error("导出失败", str(e))
    
    # ==================== 批量导入工具（折叠状态） ====================
    # Requirements: 5.1, 5.2, 5.3, 5.4
    with st.expander("📦 批量导入工具 (高级)", expanded=False):
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
    """
    渲染单个脚本卡片
    
    使用卡片容器展示脚本信息，包括：
    - 品类徽章
    - 游戏名称
    - 入库时间
    - 展开/收起查看详情
    
    Args:
        script: 脚本对象
        index: 脚本索引
        rag_system: RAG 系统实例
    
    Requirements: 4.3, 4.4, 4.5
    """
    # 卡片容器开始
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    
    # 卡片头部 - 游戏名称和品类徽章
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        game_name = script.metadata.game_name or "未命名"
        st.markdown(f'<span class="ui-h3">{game_name}</span>', unsafe_allow_html=True)
    
    with header_col2:
        # 品类徽章
        badge_html = render_badge(script.category, "primary")
        st.markdown(badge_html, unsafe_allow_html=True)
    
    # 入库时间 - 次要信息
    archived_at = script.metadata.archived_at or "未知"
    st.markdown(
        f'<span class="ui-text-secondary">入库时间: {archived_at}</span>', 
        unsafe_allow_html=True
    )
    
    # 展开/收起查看详情
    with st.expander("查看详情"):
        # 来源信息
        st.markdown(f"**来源:** {script.metadata.source}")
        
        st.markdown("---")
        st.markdown("**内容预览:**")
        content_preview = script.content[:500] + "..." if len(script.content) > 500 else script.content
        st.text(content_preview)
        
        # 删除按钮 - 右对齐
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
    
    # 卡片容器结束
    st.markdown('</div>', unsafe_allow_html=True)


def render_project_history_tab():
    """
    渲染项目历史标签页
    
    使用左右分栏布局：
    - 左侧 1/3 宽度显示项目树形列表（按客户分组）
    - 右侧 2/3 宽度显示项目详情和历史脚本时间线
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    st.markdown("### 项目历史")
    
    project_manager = st.session_state.project_manager
    
    if project_manager is None:
        display_error("项目管理器未初始化")
        return
    
    # 初始化 session state 用于存储选中的项目
    if "selected_history_project" not in st.session_state:
        st.session_state.selected_history_project = None
    
    # 获取客户列表
    try:
        clients = project_manager.list_clients()
    except Exception as e:
        display_error("获取客户列表失败", str(e))
        clients = []
    
    if not clients:
        display_info("暂无项目，请先在设置中创建项目")
        return
    
    # 左右分栏布局：1/3 项目列表，2/3 项目详情
    left_col, right_col = st.columns([1, 2])
    
    # 左侧：项目树形列表
    with left_col:
        render_project_tree(project_manager, clients)
    
    # 右侧：项目详情
    with right_col:
        render_project_detail_area(project_manager)


def render_project_tree(project_manager, clients: list):
    """
    渲染项目树形列表
    
    按客户分组显示项目，使用 expander 展开客户下的项目，
    高亮当前选中的项目。
    
    Args:
        project_manager: 项目管理器实例
        clients: 客户列表
        
    Requirements: 5.2, 5.5
    """
    st.markdown("#### 项目列表")
    
    for client in clients:
        try:
            projects = project_manager.get_projects_by_client(client)
        except Exception as e:
            display_error(f"获取 {client} 的项目列表失败", str(e))
            continue
        
        if not projects:
            continue
        
        # 使用 expander 展开客户下的项目
        with st.expander(f"{client} ({len(projects)})", expanded=True):
            for project in projects:
                project_key = f"{client}/{project.project_name}"
                is_selected = st.session_state.get("selected_history_project") == project_key
                
                # 高亮当前选中项目
                if is_selected:
                    # 使用 primary 按钮样式表示选中
                    if st.button(
                        f"● {project.project_name}",
                        key=f"proj_{project_key}",
                        use_container_width=True,
                        type="primary"
                    ):
                        st.session_state.selected_history_project = project_key
                        st.rerun()
                else:
                    # 使用默认按钮样式
                    if st.button(
                        project.project_name,
                        key=f"proj_{project_key}",
                        use_container_width=True
                    ):
                        st.session_state.selected_history_project = project_key
                        st.rerun()


def render_project_detail_area(project_manager):
    """
    渲染项目详情区域
    
    显示选中项目的信息卡片和历史脚本时间线。
    
    Args:
        project_manager: 项目管理器实例
        
    Requirements: 5.3, 5.4
    """
    selected = st.session_state.get("selected_history_project")
    
    if not selected:
        st.info("请从左侧选择项目查看详情")
        return
    
    # 解析选中的项目
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
    
    # 项目信息卡片
    render_project_info_card(project)
    
    # 历史脚本时间线
    render_scripts_timeline(project)


def render_project_info_card(project):
    """
    渲染项目信息卡片
    
    Args:
        project: 项目对象
        
    Requirements: 5.3
    """
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="ui-card-header">{project.project_name}</div>', unsafe_allow_html=True)
    
    # 项目基本信息
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
    """
    渲染历史脚本时间线
    
    使用时间线样式展示历史脚本，支持展开查看详情。
    
    Args:
        project: 项目对象
        
    Requirements: 5.4
    """
    st.markdown("#### 历史脚本")
    
    if not project.scripts_history:
        display_info("暂无历史脚本")
        return
    
    # 使用时间线样式
    st.markdown('<div class="ui-timeline">', unsafe_allow_html=True)
    
    for record in reversed(project.scripts_history):
        render_timeline_item(record)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_timeline_item(record):
    """
    渲染时间线项
    
    Args:
        record: 脚本记录对象
        
    Requirements: 5.4
    """
    st.markdown('<div class="ui-timeline-item">', unsafe_allow_html=True)
    
    # 时间和状态徽章
    status_badge = render_badge("已入库", "success") if record.is_archived else render_badge("未入库", "secondary")
    st.markdown(
        f"**版本 {record.version}** · {record.created_at[:10]} {status_badge}",
        unsafe_allow_html=True
    )
    
    # 内容预览（使用 expander）
    with st.expander("查看内容"):
        # 元数据展示
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(f"**创建时间:** {record.created_at}")
        with meta_col2:
            # 使用徽章显示入库状态
            detail_status_badge = render_badge("已入库", "success") if record.is_archived else render_badge("未入库", "secondary")
            st.markdown(f"**入库状态:** {detail_status_badge}", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 如果有解析后的输出，显示表格
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
            # 显示内容预览
            content_preview = record.content[:300] + "..." if len(record.content) > 300 else record.content
            st.text(content_preview)
    
    st.markdown('</div>', unsafe_allow_html=True)


# ==================== 设置页面 ====================
def render_settings_page():
    """
    渲染设置页面 - 垂直 Tabs 布局
    
    使用左右分栏模拟垂直 tabs，左侧为设置菜单，右侧为设置内容区域。
    整合 API 配置和提示词管理功能。
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 8.1, 8.2, 8.3, 8.4
    """
    st.markdown("## 设置")
    
    # 初始化设置页面的 session state
    if "selected_setting" not in st.session_state:
        st.session_state.selected_setting = "API 配置"
    
    # 使用左右分栏模拟垂直 tabs
    # Requirements: 6.1
    left_col, right_col = st.columns([1, 3])
    
    with left_col:
        # 左侧设置菜单卡片
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<div class="ui-card-header">设置菜单</div>', unsafe_allow_html=True)
        
        # 设置菜单选项（使用 radio 模拟垂直 tabs）
        settings_options = ["API 配置", "提示词管理"]
        selected_setting = st.radio(
            "设置项",
            settings_options,
            index=settings_options.index(st.session_state.selected_setting) if st.session_state.selected_setting in settings_options else 0,
            label_visibility="collapsed",
            key="settings_menu_radio"
        )
        
        # 更新 session state
        if selected_setting != st.session_state.selected_setting:
            st.session_state.selected_setting = selected_setting
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with right_col:
        # 右侧设置内容区域
        if st.session_state.selected_setting == "API 配置":
            render_api_settings_card()
        elif st.session_state.selected_setting == "提示词管理":
            render_prompt_settings_card()


def render_api_settings_card():
    """
    渲染 API 配置卡片（设置页面版本）
    
    使用卡片包裹配置区域，配置列表使用表格展示，
    新增/编辑表单放在列表下方。
    
    Requirements: 6.2, 6.3, 6.4, 8.2, 8.4
    """
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
    
    # API 配置卡片
    # Requirements: 6.2
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">API 配置</div>', unsafe_allow_html=True)
    
    # 配置列表表格
    # Requirements: 6.3
    if all_configs:
        st.markdown("#### 已有配置")
        
        # 构建配置数据表格
        config_data = []
        for config in all_configs:
            status = "✓ 当前" if config.name == active_config_name else ""
            embedding_info = config.embedding_model if config.has_embedding_config() else "未配置"
            config_data.append({
                "配置名称": config.name,
                "模型": config.model_id,
                "Embedding": embedding_info,
                "状态": status
            })
        
        # 使用 dataframe 展示配置列表
        import pandas as pd
        df = pd.DataFrame(config_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 配置选择和操作
        col1, col2, col3 = st.columns([2, 1, 1])
        
        config_names = [config.name for config in all_configs]
        
        # 确保当前活动配置在列表中
        if active_config_name not in config_names and config_names:
            active_config_name = config_names[0]
        
        with col1:
            selected_config_name = st.selectbox(
                "选择配置",
                config_names,
                index=config_names.index(active_config_name) if active_config_name in config_names else 0,
                help="选择要使用或编辑的 API 配置",
                key="settings_config_select"
            )
        
        with col2:
            # 切换配置按钮
            if st.button("切换到此配置", key="settings_switch_config", use_container_width=True, type="primary"):
                if selected_config_name != active_config_name:
                    try:
                        success, msg = api_manager.switch_config(selected_config_name)
                        if success:
                            # 更新 RAG 系统的 API 管理器
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
            # 删除配置按钮
            if len(all_configs) > 1:  # 至少保留一个配置
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
    # Requirements: 6.4
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">添加/编辑配置</div>', unsafe_allow_html=True)
    
    # 配置表单
    with st.form("settings_api_config_form"):
        # 如果选择了现有配置，预填充表单
        edit_config = None
        if all_configs and current_config:
            edit_config = current_config
        
        col1, col2 = st.columns(2)
        
        with col1:
            config_name = st.text_input(
                "配置名称",
                value=edit_config.name if edit_config else "",
                help="为此配置起一个名称，方便管理多个 API 配置"
            )
            api_key = st.text_input(
                "API Key",
                value=edit_config.api_key if edit_config else "",
                type="password",
                help="您的 API 密钥，支持 OpenAI 及兼容格式的 API"
            )
        
        with col2:
            base_url = st.text_input(
                "Base URL",
                value=edit_config.base_url if edit_config else "https://api.openai.com/v1",
                help="API 服务地址，如 OpenAI、文心一言、豆包等"
            )
            model_id = st.text_input(
                "Model ID",
                value=edit_config.model_id if edit_config else "gpt-4",
                help="模型标识符，如 gpt-4、gpt-3.5-turbo 等"
            )
        
        # Embedding 模型配置
        st.markdown("---")
        st.markdown("#### Embedding 模型 (知识库向量检索)")
        
        from src.api_manager import EMBEDDING_MODELS
        
        # 获取当前配置的 embedding 信息
        current_embedding_provider = ""
        current_embedding_model = ""
        if edit_config and edit_config.embedding_model:
            # 根据 embedding_base_url 判断当前 provider
            emb_url = edit_config.embedding_base_url or ""
            if "volces.com" in emb_url or "ark" in emb_url:
                current_embedding_provider = "doubao"
            elif "siliconflow" in emb_url:
                current_embedding_provider = "siliconflow"
            else:
                current_embedding_provider = "openai"
            current_embedding_model = edit_config.embedding_model
        
        # Embedding 提供商选择
        embedding_providers = ["不使用"] + list(EMBEDDING_MODELS.keys())
        provider_names = ["不使用"] + [EMBEDDING_MODELS[k]["name"] for k in EMBEDDING_MODELS.keys()]
        
        # 找到当前 provider 的索引
        provider_idx = 0
        if current_embedding_provider in embedding_providers:
            provider_idx = embedding_providers.index(current_embedding_provider)
        
        emb_col1, emb_col2 = st.columns(2)
        
        with emb_col1:
            selected_provider_name = st.selectbox(
                "Embedding 提供商",
                provider_names,
                index=provider_idx,
                help="选择 Embedding 模型提供商，用于知识库向量检索"
            )
        
        # 获取选中的 provider key
        selected_provider = ""
        if selected_provider_name != "不使用":
            for k, v in EMBEDDING_MODELS.items():
                if v["name"] == selected_provider_name:
                    selected_provider = k
                    break
        
        # Embedding 模型选择
        embedding_model = ""
        embedding_base_url = ""
        embedding_api_key = ""
        
        if selected_provider and selected_provider in EMBEDDING_MODELS:
            provider_info = EMBEDDING_MODELS[selected_provider]
            model_options = provider_info["models"]
            model_names = [m["name"] for m in model_options]
            model_ids = [m["id"] for m in model_options]
            
            # 找到当前模型的索引
            model_idx = 0
            if current_embedding_model in model_ids:
                model_idx = model_ids.index(current_embedding_model)
            
            with emb_col2:
                selected_model_name = st.selectbox(
                    "Embedding 模型",
                    model_names,
                    index=model_idx,
                    help="选择具体的 Embedding 模型"
                )
            
            # 获取选中的模型 ID
            for m in model_options:
                if m["name"] == selected_model_name:
                    embedding_model = m["id"]
                    break
            
            embedding_base_url = provider_info["base_url"]
            
            st.caption(f"API 地址: {embedding_base_url}")
            
            # Embedding API Key（如果与 LLM 提供商不同，需要单独填写）
            embedding_api_key = st.text_input(
                "Embedding API Key",
                value=edit_config.embedding_api_key if edit_config else "",
                type="password",
                help="如果 Embedding 提供商与 LLM 不同，请填写对应的 API Key。留空则使用上方的 API Key"
            )
        
        # 操作按钮 - 右对齐
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            test_btn = st.form_submit_button("测试连接", use_container_width=True)
        with col3:
            save_btn = st.form_submit_button("保存配置", use_container_width=True)
    
    if save_btn:
        # 验证输入
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
                    # 自动切换到新保存的配置
                    api_manager.switch_config(config_name.strip())
                    # 更新 RAG 系统的 API 管理器
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
                    # 临时保存配置用于测试
                    config = APIConfig(
                        api_key=api_key.strip(),
                        base_url=base_url.strip(),
                        model_id=model_id.strip(),
                        name=config_name.strip()
                    )
                    # 临时切换配置进行测试
                    original_config = api_manager.load_config()
                    api_manager.save_config(config)
                    api_manager.switch_config(config_name.strip())
                    
                    success, msg = api_manager.test_connection()
                    
                    # 恢复原配置
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
    """
    渲染提示词管理卡片（设置页面版本）
    
    使用卡片包裹提示词管理区域。
    
    Requirements: 6.2, 8.3, 8.4
    """
    api_manager = st.session_state.api_manager
    
    if api_manager is None:
        display_error("API 管理器未初始化")
        return
    
    from src.prompts import PromptManager
    
    # 设置 API 管理器引用
    PromptManager.set_api_manager(api_manager)
    
    # 提示词管理卡片
    # Requirements: 6.2
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="ui-card-header">提示词管理</div>', unsafe_allow_html=True)
    
    st.caption("修改提示词可以调整脚本生成的风格和输出格式")
    
    # 提示词类型选择
    prompt_types = {
        "draft": "脚本生成",
        "review": "脚本评审", 
        "refine": "脚本修正"
    }
    
    selected_type = st.selectbox(
        "选择提示词类型",
        list(prompt_types.keys()),
        format_func=lambda x: prompt_types[x],
        help="选择要编辑的提示词类型",
        key="settings_prompt_type"
    )
    
    # 获取当前提示词（自定义或默认）
    custom_prompt = api_manager.get_prompt(selected_type)
    default_prompt = PromptManager.get_default_template(selected_type)
    
    current_prompt = custom_prompt if custom_prompt else default_prompt
    is_custom = custom_prompt is not None
    
    # 显示状态
    if is_custom:
        st.info("当前使用自定义提示词")
    else:
        st.info("当前使用默认提示词")
    
    # 提示词编辑区
    st.markdown("#### 提示词内容")
    st.caption("可用变量: {game_intro}, {usp}, {target_audience}, {category}, {references}, {script}, {review_feedback}")
    
    edited_prompt = st.text_area(
        "编辑提示词",
        value=current_prompt,
        height=400,
        key=f"settings_prompt_editor_{selected_type}",
        label_visibility="collapsed"
    )
    
    # 操作按钮 - 右对齐
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
    """
    主程序入口
    
    使用导航菜单路由到不同页面，包括设置页面。
    
    Requirements: 4.5, 8.1
    """
    # 注入自定义 CSS
    inject_custom_css()
    
    # 检查系统健康状态
    is_healthy, errors = check_system_health()
    
    if not is_healthy:
        st.markdown("# 游戏广告脚本生成器")
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
    
    # 渲染导航菜单并获取选中页面
    selected_page = render_navigation()
    
    # 根据选中页面渲染对应内容
    if selected_page == "脚本生成":
        render_script_generation_page()
    elif selected_page == "知识库":
        render_knowledge_base_page()
    elif selected_page == "项目历史":
        render_project_history_page()
    elif selected_page == "设置":
        render_settings_page()


def render_script_generation_page():
    """渲染脚本生成页面"""
    # 显示当前项目信息
    if st.session_state.current_project:
        current = st.session_state.current_project
        st.markdown(f"**当前项目:** {current.client_name} / {current.project_name}")
    
    render_script_generation_tab()


def render_knowledge_base_page():
    """渲染知识库页面"""
    render_knowledge_base_tab()


def render_project_history_page():
    """渲染项目历史页面"""
    render_project_history_tab()


if __name__ == "__main__":
    main()
