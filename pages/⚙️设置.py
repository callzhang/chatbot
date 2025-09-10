"""
Settings page for Stardust.ai Chatbot
Integrates theme management, mobile optimization, analytics, and RAG features
"""

import streamlit as st
from tools import theme, mobile, analytics, rag
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="设置 - 星尘小助手",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize theme
theme.initialize_theme()

# Main title
st.title("⚙️ 星尘小助手设置")
st.markdown("个性化您的AI助手体验")

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🎛️ 设置选项")
    
    setting_tabs = {
        "🎨 主题设置": "theme",
        "📱 移动端": "mobile", 
        "📊 数据分析": "analytics",
        "📚 文档管理": "rag",
        "🔧 高级设置": "advanced"
    }
    
    selected_tab = st.radio(
        "选择设置类别",
        options=list(setting_tabs.keys()),
        key="settings_tab"
    )

# Get selected tab
current_tab = setting_tabs[selected_tab]

# Theme Settings Tab
if current_tab == "theme":
    st.header("🎨 主题设置")
    
    # Theme selector
    theme.create_theme_selector()
    
    # Apply current theme CSS
    theme.apply_theme_css()
    
    # Theme customization
    st.subheader("🎨 自定义主题")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 颜色设置")
        current_theme = theme.get_current_theme()
        theme_config = theme.get_theme_config()
        
        primary_color = st.color_picker(
            "主色调",
            value=theme_config['primaryColor'],
            key="custom_primary_color"
        )
        
        background_color = st.color_picker(
            "背景色",
            value=theme_config['backgroundColor'],
            key="custom_background_color"
        )
    
    with col2:
        secondary_bg = st.color_picker(
            "次要背景色",
            value=theme_config['secondaryBackgroundColor'],
            key="custom_secondary_bg"
        )
        
        text_color = st.color_picker(
            "文字颜色",
            value=theme_config['textColor'],
            key="custom_text_color"
        )
    
    # Font settings
    st.markdown("#### 字体设置")
    font_family = st.selectbox(
        "字体",
        ["sans serif", "serif", "monospace"],
        index=0,
        key="custom_font"
    )
    
    # Save custom theme
    if st.button("💾 保存自定义主题"):
        custom_theme = {
            "primaryColor": primary_color,
            "backgroundColor": background_color,
            "secondaryBackgroundColor": secondary_bg,
            "textColor": text_color,
            "font": font_family
        }
        
        # Add to themes (in production, save to database)
        theme_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        theme.THEMES[theme_name] = custom_theme
        theme.set_theme(theme_name)
        
        st.success(f"✅ 自定义主题 '{theme_name}' 已保存")
        st.rerun()
    
    # Theme export/import
    st.markdown("#### 📤 主题管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 导出当前主题"):
            theme_config = theme.export_theme_config()
            st.download_button(
                label="下载主题配置",
                data=theme_config,
                file_name=f"stardust_theme_{current_theme}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_theme = st.file_uploader(
            "📥 导入主题",
            type=['json'],
            help="上传主题配置文件"
        )
        
        if uploaded_theme:
            theme_data = uploaded_theme.read().decode('utf-8')
            if theme.import_theme_config(theme_data):
                st.success("✅ 主题导入成功")
                st.rerun()
            else:
                st.error("❌ 主题导入失败，请检查文件格式")

# Mobile Settings Tab
elif current_tab == "mobile":
    st.header("📱 移动端优化")
    
    # Mobile detection
    is_mobile = mobile.detect_mobile_device()
    st.info(f"📱 检测到设备类型: {'移动设备' if is_mobile else '桌面设备'}")
    
    # Mobile optimizations
    mobile.apply_mobile_optimizations()
    
    # Mobile settings
    mobile.create_mobile_settings()
    
    # Mobile navigation demo
    st.subheader("📱 移动端导航预览")
    if st.button("预览移动端界面"):
        with st.expander("移动端界面预览", expanded=True):
            mobile.create_mobile_optimized_chat()
    
    # Mobile analytics
    st.subheader("📊 移动端使用统计")
    mobile.create_mobile_analytics()
    
    # Export mobile config
    if st.button("📤 导出移动端配置"):
        config = mobile.export_mobile_config()
        st.download_button(
            label="下载移动端配置",
            data=json.dumps(config, indent=2, ensure_ascii=False),
            file_name="mobile_config.json",
            mime="application/json"
        )

# Analytics Tab
elif current_tab == "analytics":
    st.header("📊 数据分析")
    
    # Analytics dashboard
    analytics.create_analytics_dashboard()
    
    # User analytics
    st.markdown("---")
    analytics.create_user_analytics()
    
    # Analytics settings
    st.markdown("---")
    analytics.create_analytics_settings()

# RAG/Document Management Tab
elif current_tab == "rag":
    st.header("📚 文档管理")
    
    # RAG interface
    rag.create_rag_interface()
    
    # RAG analytics
    st.markdown("---")
    rag.create_rag_analytics()
    
    # Export RAG data
    st.markdown("---")
    st.subheader("📤 数据导出")
    if st.button("导出RAG数据"):
        try:
            filename = rag.export_rag_data()
            st.success(f"✅ 数据已导出到 {filename}")
        except Exception as e:
            st.error(f"❌ 导出失败: {e}")

# Advanced Settings Tab
elif current_tab == "advanced":
    st.header("🔧 高级设置")
    
    # System settings
    st.subheader("⚙️ 系统设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 性能设置")
        cache_enabled = st.checkbox("启用缓存", value=True, key="cache_enabled")
        max_cache_size = st.slider("最大缓存大小 (MB)", 10, 1000, 100, key="max_cache_size")
        auto_refresh = st.checkbox("自动刷新", value=False, key="auto_refresh")
        refresh_interval = st.slider("刷新间隔 (秒)", 30, 3600, 300, key="refresh_interval")
    
    with col2:
        st.markdown("#### 安全设置")
        enable_logging = st.checkbox("启用日志记录", value=True, key="enable_logging")
        log_level = st.selectbox("日志级别", ["DEBUG", "INFO", "WARNING", "ERROR"], key="log_level")
        data_retention = st.slider("数据保留天数", 7, 365, 30, key="data_retention")
        enable_backup = st.checkbox("启用自动备份", value=True, key="enable_backup")
    
    # API settings
    st.subheader("🔌 API设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### OpenAI设置")
        openai_timeout = st.slider("请求超时 (秒)", 10, 120, 30, key="openai_timeout")
        max_tokens = st.slider("最大令牌数", 1000, 8000, 4000, key="max_tokens")
        temperature = st.slider("温度", 0.0, 2.0, 0.7, key="temperature")
    
    with col2:
        st.markdown("#### 其他API设置")
        bing_enabled = st.checkbox("启用Bing搜索", value=True, key="bing_enabled")
        google_enabled = st.checkbox("启用Google服务", value=False, key="google_enabled")
        rate_limit = st.slider("请求频率限制 (次/分钟)", 10, 100, 30, key="rate_limit")
    
    # Database settings
    st.subheader("🗄️ 数据库设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_type = st.selectbox("数据库类型", ["SQLite", "PostgreSQL", "MySQL"], key="db_type")
        if db_type != "SQLite":
            db_host = st.text_input("数据库主机", key="db_host")
            db_port = st.number_input("端口", value=5432, key="db_port")
            db_name = st.text_input("数据库名称", key="db_name")
    
    with col2:
        if db_type != "SQLite":
            db_user = st.text_input("用户名", key="db_user")
            db_password = st.text_input("密码", type="password", key="db_password")
        
        backup_frequency = st.selectbox("备份频率", ["每日", "每周", "每月"], key="backup_frequency")
        auto_cleanup = st.checkbox("自动清理旧数据", value=True, key="auto_cleanup")
    
    # Export/Import settings
    st.subheader("📤 设置管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 导出所有设置"):
            settings = {
                "theme": theme.get_current_theme(),
                "mobile": mobile.export_mobile_config(),
                "analytics": {
                    "enabled": st.session_state.get("analytics_enabled", True),
                    "performance_monitoring": st.session_state.get("performance_monitoring", True)
                },
                "advanced": {
                    "cache_enabled": st.session_state.get("cache_enabled", True),
                    "max_cache_size": st.session_state.get("max_cache_size", 100),
                    "openai_timeout": st.session_state.get("openai_timeout", 30),
                    "max_tokens": st.session_state.get("max_tokens", 4000)
                }
            }
            
            st.download_button(
                label="下载设置文件",
                data=json.dumps(settings, indent=2, ensure_ascii=False),
                file_name=f"stardust_settings_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_settings = st.file_uploader(
            "📥 导入设置",
            type=['json'],
            help="上传设置配置文件"
        )
        
        if uploaded_settings:
            try:
                settings_data = json.loads(uploaded_settings.read().decode('utf-8'))
                
                # Apply settings
                if "theme" in settings_data:
                    theme.set_theme(settings_data["theme"])
                
                if "mobile" in settings_data:
                    mobile.import_mobile_config(settings_data["mobile"])
                
                st.success("✅ 设置导入成功")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 设置导入失败: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🌟 星尘小助手 - 让AI更智能，让生活更美好</p>
        <p>版本 2.0.0 | 最后更新: 2024年1月</p>
    </div>
    """,
    unsafe_allow_html=True
)
