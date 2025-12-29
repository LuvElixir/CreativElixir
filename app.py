"""
游戏信息流广告脚本自动化工具 - 主应用入口

基于 Streamlit 构建的 AI 驱动广告脚本生成工具。
"""

import streamlit as st
from pathlib import Path
import traceback
from typing import Optional, Tuple

# 导入核心模块
from src.api_manager import APIManager, APIConfig
from src.rag_system import RAGSystem
from src.project_manager import ProjectManager, Project
from src.script_generator import ScriptGenerator, GenerationInput, parse_script_output

# 页面配置
st.set_page_config(
    page_title="游戏广告脚本生成器",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== 错误处理工具函数 ====================
def display_error(message: str, details: Optional[str] = None):
    """
    显示用户友好的错误信息
    
    Args:
        message: 主要错误信息
        details: 可选的详细信息
    """
    st.error(f"❌ {message}")
    if details:
        with st.expander("查看详细信息"):
            st.code(details)


def display_warning(message: str):
    """显示警告信息"""
    st.warning(f"⚠️ {message}")


def display_success(message: str):
    """显示成功信息"""
    st.success(f"✅ {message}")


def display_info(message: str):
    """显示提示信息"""
    st.info(f"ℹ️ {message}")


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
        st.markdown("# 🎮 游戏广告脚本生成器")
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


def render_api_settings():
    """渲染 API 设置区域"""
    with st.expander("⚙️ API 设置", expanded=False):
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
                config_info = f"✅ 当前配置: {current_config.name} ({current_config.model_id})"
                if current_config.has_embedding_config():
                    config_info += f"\n📊 Embedding: {current_config.embedding_model}"
                st.info(config_info)
            
            # 删除配置按钮
            if len(all_configs) > 1:  # 至少保留一个配置
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️ 删除", key="delete_config"):
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
                
                st.caption(f"📍 API 地址: {embedding_base_url}")
                
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
                save_btn = st.form_submit_button("💾 保存配置", use_container_width=True)
            with col2:
                test_btn = st.form_submit_button("🔗 测试连接", use_container_width=True)
        
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
    with st.expander("📝 提示词管理", expanded=False):
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
            st.info("📝 当前使用自定义提示词")
        else:
            st.info("📋 当前使用默认提示词")
        
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
            if st.button("💾 保存", use_container_width=True, key=f"save_prompt_{selected_type}"):
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
            if st.button("🔄 重置", use_container_width=True, key=f"reset_prompt_{selected_type}"):
                success, msg = api_manager.reset_prompt(selected_type)
                if success:
                    display_success("已重置为默认提示词")
                    st.rerun()
                else:
                    display_error(f"重置失败: {msg}")
        
        with col3:
            if st.button("📋 复制默认", use_container_width=True, key=f"copy_default_{selected_type}"):
                st.session_state[f"prompt_editor_{selected_type}"] = default_prompt
                st.rerun()


def render_project_management():
    """渲染项目管理区域"""
    with st.expander("📁 项目管理", expanded=False):
        project_manager = st.session_state.project_manager
        
        if project_manager is None:
            display_error("项目管理器未初始化", st.session_state.get('init_error_project'))
            return
        
        # 创建新项目
        st.markdown("#### 创建新项目")
        with st.form("create_project_form"):
            new_client = st.text_input("客户名称", help="客户或公司名称")
            new_project = st.text_input("项目名称", help="项目或游戏名称")
            create_btn = st.form_submit_button("➕ 创建项目", use_container_width=True)
        
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
                            if st.button("📂 加载项目", use_container_width=True):
                                st.session_state.current_project = project
                                display_success(f"已加载项目: {selected_client}/{selected_project}")
                                st.rerun()
                            
                            if st.button("🗑️ 删除项目", use_container_width=True):
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
            st.info(f"📌 {current.client_name} / {current.project_name}")


def render_knowledge_base_management():
    """渲染知识库管理区域"""
    with st.expander("📚 知识库管理", expanded=False):
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
                    st.caption(f"🟢 向量检索已启用 ({provider_name}: {api_config.embedding_model})")
                else:
                    st.caption("🟡 向量数据库已安装，请配置 Embedding 模型")
            else:
                st.caption("🔴 向量数据库未安装")
        except Exception as e:
            display_error("获取知识库状态失败", str(e))
        
        st.markdown("---")
        
        # 导出知识库
        st.markdown("#### 导出知识库")
        if st.button("📤 导出为 ZIP", use_container_width=True):
            with st.spinner("正在导出..."):
                try:
                    export_path = "./data/knowledge_base_export"
                    success, result = rag_system.export_knowledge_base(export_path)
                    if success:
                        # 提供下载
                        try:
                            with open(result, "rb") as f:
                                st.download_button(
                                    label="⬇️ 下载导出文件",
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
            if st.button("📥 导入知识库", use_container_width=True):
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
    tabs = st.tabs(["📝 脚本生成", "📚 知识库", "📊 项目历史"])
    
    with tabs[0]:
        render_script_generation_tab()
    
    with tabs[1]:
        render_knowledge_base_tab()
    
    with tabs[2]:
        render_project_history_tab()


def render_script_generation_tab():
    """渲染脚本生成标签页"""
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
    
    # 输入区域
    col1, col2 = st.columns(2)
    
    with col1:
        game_intro = st.text_area(
            "游戏介绍",
            height=150,
            placeholder="请输入游戏的基本介绍，包括游戏类型、玩法特点等...",
            value=st.session_state.current_project.game_intro if st.session_state.current_project else "",
            help="详细描述游戏的核心玩法和特色"
        )
        
        usp = st.text_area(
            "独特卖点 (USP)",
            height=100,
            placeholder="请输入游戏的独特卖点，如创新玩法、独特美术风格等...",
            value=st.session_state.current_project.usp if st.session_state.current_project else "",
            help="游戏区别于竞品的核心优势"
        )
    
    with col2:
        target_audience = st.text_area(
            "目标人群",
            height=100,
            placeholder="请描述目标用户群体，如年龄、性别、游戏偏好等...",
            value=st.session_state.current_project.target_audience if st.session_state.current_project else "",
            help="广告投放的目标受众特征"
        )
        
        try:
            categories = st.session_state.rag_system.get_categories()
        except Exception:
            categories = ["SLG", "MMO", "休闲", "卡牌", "二次元", "模拟经营"]
        
        default_category = st.session_state.current_project.category if st.session_state.current_project else ""
        default_idx = categories.index(default_category) if default_category in categories else 0
        
        category = st.selectbox(
            "游戏品类",
            categories,
            index=default_idx,
            help="选择游戏所属品类，用于检索同品类参考脚本"
        )
    
    # 生成按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button("🚀 生成脚本", use_container_width=True, type="primary")
    
    # 生成逻辑
    if generate_btn:
        # 验证输入
        is_valid, error_msg = validate_generation_input(game_intro, usp, target_audience, category)
        if not is_valid:
            display_error(error_msg)
            return
        
        # 更新当前项目信息
        if st.session_state.current_project:
            try:
                project = st.session_state.current_project
                project.game_intro = game_intro
                project.usp = usp
                project.target_audience = target_audience
                project.category = category
                st.session_state.project_manager.update_project(project)
            except Exception as e:
                display_warning(f"更新项目信息失败: {str(e)}")
        
        # 创建生成输入
        input_data = GenerationInput(
            game_intro=game_intro,
            usp=usp,
            target_audience=target_audience,
            category=category
        )
        
        # 创建生成器
        try:
            generator = ScriptGenerator(
                api_manager=api_manager,
                rag_system=st.session_state.rag_system
            )
        except Exception as e:
            display_error("初始化脚本生成器失败", str(e))
            return
        
        # 流式输出区域
        output_container = st.empty()
        full_output = ""
        
        with st.spinner("正在生成脚本..."):
            try:
                gen = generator.generate(input_data)
                for chunk in gen:
                    full_output += chunk
                    output_container.markdown(full_output)
                
                # 获取最终输出
                try:
                    output = gen.send(None)
                except StopIteration as e:
                    output = e.value
                
                st.session_state.generated_script = full_output
                st.session_state.generation_output = output
                st.session_state.last_error = None
                
            except Exception as e:
                st.session_state.last_error = str(e)
                display_error("脚本生成失败", str(e))
    
    # 显示生成结果
    if st.session_state.generation_output:
        st.markdown("---")
        st.markdown("### 生成结果")
        
        output = st.session_state.generation_output
        
        if output.is_valid():
            # 显示三栏表格
            st.markdown(output.to_markdown_table())
            
            # 入库按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📥 入库", use_container_width=True):
                    try:
                        # 确定品类
                        archive_category = category if 'category' in dir() else (
                            st.session_state.current_project.category if st.session_state.current_project else "SLG"
                        )
                        
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
                                    "storyboard": output.storyboard,
                                    "voiceover": output.voiceover,
                                    "design_intent": output.design_intent
                                }
                            )
                        
                        display_success("脚本已入库！")
                    except Exception as e:
                        display_error("入库失败", str(e))
        else:
            # 显示原始内容
            st.markdown("**原始输出:**")
            st.text(output.raw_content)
            display_warning("脚本格式解析失败，显示原始内容。您可以手动复制并编辑。")


def render_knowledge_base_tab():
    """渲染知识库标签页"""
    st.markdown("### 知识库浏览")
    
    rag_system = st.session_state.rag_system
    
    if rag_system is None:
        display_error("知识库系统未初始化")
        return
    
    try:
        categories = rag_system.get_categories()
    except Exception as e:
        display_error("获取品类列表失败", str(e))
        categories = []
    
    # 品类筛选
    selected_category = st.selectbox("选择品类", ["全部"] + categories)
    
    # 获取脚本列表
    try:
        if selected_category == "全部":
            scripts = []
            for cat in categories:
                scripts.extend(rag_system.get_scripts_by_category(cat))
        else:
            scripts = rag_system.get_scripts_by_category(selected_category)
    except Exception as e:
        display_error("获取脚本列表失败", str(e))
        scripts = []
    
    # 显示脚本数量
    display_info(f"共 {len(scripts)} 个脚本")
    
    # 显示脚本列表
    if scripts:
        for i, script in enumerate(scripts):
            with st.expander(f"📄 脚本 {i+1} - {script.category} ({script.metadata.game_name or '未命名'})"):
                st.markdown(f"**品类:** {script.category}")
                st.markdown(f"**来源:** {script.metadata.source}")
                st.markdown(f"**入库时间:** {script.metadata.archived_at}")
                st.markdown("---")
                st.markdown("**内容:**")
                st.text(script.content[:500] + "..." if len(script.content) > 500 else script.content)
                
                # 删除按钮
                if st.button(f"🗑️ 删除", key=f"delete_script_{script.id}"):
                    try:
                        if rag_system.delete_script(script.id):
                            display_success("脚本已删除")
                            st.rerun()
                        else:
                            display_error("删除失败，脚本可能不存在")
                    except Exception as e:
                        display_error("删除脚本时发生错误", str(e))
    else:
        display_info("暂无脚本数据")
    
    st.markdown("---")
    
    # 导入导出按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 导出知识库", use_container_width=True):
            with st.spinner("正在导出..."):
                try:
                    export_path = "./data/knowledge_base_export"
                    success, result = rag_system.export_knowledge_base(export_path)
                    if success:
                        with open(result, "rb") as f:
                            st.download_button(
                                label="⬇️ 下载",
                                data=f,
                                file_name="knowledge_base.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                    else:
                        display_error(result)
                except Exception as e:
                    display_error("导出失败", str(e))
    
    with col2:
        uploaded = st.file_uploader("导入知识库", type=["zip"], key="kb_tab_import", label_visibility="collapsed")
        if uploaded:
            if st.button("📥 确认导入", use_container_width=True):
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


def render_project_history_tab():
    """渲染项目历史标签页"""
    st.markdown("### 项目历史")
    
    project_manager = st.session_state.project_manager
    
    if project_manager is None:
        display_error("项目管理器未初始化")
        return
    
    # 项目选择
    try:
        clients = project_manager.list_clients()
    except Exception as e:
        display_error("获取客户列表失败", str(e))
        clients = []
    
    if not clients:
        display_info("暂无项目，请先在侧边栏创建项目")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_client = st.selectbox("选择客户", clients, key="history_client")
    
    with col2:
        if selected_client:
            try:
                projects = project_manager.get_projects_by_client(selected_client)
                project_names = [p.project_name for p in projects]
            except Exception as e:
                display_error("获取项目列表失败", str(e))
                project_names = []
            
            selected_project = st.selectbox("选择项目", project_names, key="history_project") if project_names else None
        else:
            selected_project = None
    
    if selected_client and selected_project:
        try:
            project = project_manager.get_project(selected_client, selected_project)
        except Exception as e:
            display_error("加载项目失败", str(e))
            project = None
        
        if project:
            # 显示项目信息
            st.markdown("---")
            st.markdown("#### 项目信息")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**客户:** {project.client_name}")
                st.markdown(f"**项目:** {project.project_name}")
                st.markdown(f"**品类:** {project.category or '未设置'}")
            with col2:
                st.markdown(f"**创建时间:** {project.created_at[:10]}")
                st.markdown(f"**更新时间:** {project.updated_at[:10]}")
            
            # 显示历史脚本
            st.markdown("---")
            st.markdown("#### 历史脚本")
            
            if project.scripts_history:
                for record in reversed(project.scripts_history):
                    with st.expander(f"📄 版本 {record.version} - {record.created_at[:10]}"):
                        st.markdown(f"**创建时间:** {record.created_at}")
                        st.markdown(f"**是否入库:** {'是' if record.is_archived else '否'}")
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
                                    st.text(record.content)
                            except Exception:
                                st.text(record.content)
                        else:
                            st.text(record.content)
            else:
                display_info("暂无历史脚本")


# ==================== 主程序入口 ====================
def main():
    """主程序入口"""
    # 检查系统健康状态
    is_healthy, errors = check_system_health()
    
    if not is_healthy:
        st.markdown("# 🎮 游戏广告脚本生成器")
        st.markdown("---")
        st.markdown("### ⚠️ 系统初始化错误")
        for error in errors:
            display_error(error)
        st.markdown("---")
        st.markdown("请检查以下内容：")
        st.markdown("1. 确保 `./data` 目录存在且有写入权限")
        st.markdown("2. 检查依赖是否正确安装")
        st.markdown("3. 重启应用后重试")
        return
    
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
