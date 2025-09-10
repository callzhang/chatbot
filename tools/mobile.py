"""
Mobile optimization utilities for Stardust.ai Chatbot
Provides responsive design and mobile-specific features
"""

import streamlit as st
from typing import Dict, Any
import json

# Mobile-specific CSS
MOBILE_CSS = """
<style>
/* Mobile-first responsive design */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
        margin-top: 1rem !important;
    }
    
    .stChatMessage {
        margin: 0.25rem 0 !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput > div > div > input {
        font-size: 16px !important; /* Prevents zoom on iOS */
    }
    
    .stSelectbox > div > div {
        font-size: 16px !important;
    }
    
    .stButton > button {
        width: 100% !important;
        margin: 0.25rem 0 !important;
    }
    
    .stSidebar {
        width: 100% !important;
        position: fixed !important;
        top: 0 !important;
        left: -100% !important;
        height: 100vh !important;
        z-index: 1000 !important;
        transition: left 0.3s ease !important;
    }
    
    .stSidebar:not([aria-expanded="false"]) {
        left: 0 !important;
    }
    
    .mobile-menu-toggle {
        position: fixed;
        top: 1rem;
        left: 1rem;
        z-index: 1001;
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 20px;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .mobile-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: var(--primary-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .mobile-content {
        margin-top: 60px !important;
        padding-bottom: 80px !important; /* Space for mobile navigation */
    }
    
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: white;
        border-top: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 999;
    }
    
    .mobile-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-decoration: none;
        color: #666;
        font-size: 12px;
        padding: 0.5rem;
    }
    
    .mobile-nav-item.active {
        color: var(--primary-color);
    }
    
    .mobile-nav-item i {
        font-size: 20px;
        margin-bottom: 0.25rem;
    }
    
    /* Touch-friendly buttons */
    .touch-button {
        min-height: 44px !important;
        min-width: 44px !important;
        padding: 0.75rem !important;
    }
    
    /* Swipe gestures */
    .swipe-container {
        touch-action: pan-x;
        overflow-x: hidden;
    }
    
    /* Mobile chat optimizations */
    .chat-container {
        height: calc(100vh - 120px) !important;
        overflow-y: auto !important;
    }
    
    .chat-input {
        position: fixed !important;
        bottom: 60px !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 1rem !important;
        border-top: 1px solid #e0e0e0 !important;
        z-index: 998 !important;
    }
}

/* Tablet optimizations */
@media (min-width: 769px) and (max-width: 1024px) {
    .main .block-container {
        max-width: 90% !important;
        padding: 1.5rem !important;
    }
    
    .stSidebar {
        width: 300px !important;
    }
}

/* Desktop optimizations */
@media (min-width: 1025px) {
    .main .block-container {
        max-width: 1200px !important;
    }
}

/* PWA optimizations */
@media (display-mode: standalone) {
    .mobile-header {
        padding-top: env(safe-area-inset-top);
    }
    
    .mobile-nav {
        padding-bottom: env(safe-area-inset-bottom);
    }
}
</style>
"""

# Mobile navigation items
MOBILE_NAV_ITEMS = [
    {"icon": "💬", "label": "聊天", "page": "chat"},
    {"icon": "⭐", "label": "应用", "page": "apps"},
    {"icon": "📒", "label": "历史", "page": "history"},
    {"icon": "⚙️", "label": "设置", "page": "settings"}
]

def apply_mobile_optimizations():
    """Apply mobile CSS optimizations"""
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)

def create_mobile_header():
    """Create mobile header component"""
    header_html = """
    <div class="mobile-header">
        <h1 style="margin: 0; font-size: 18px;">🌟 星尘小助手</h1>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def create_mobile_menu_toggle():
    """Create mobile menu toggle button"""
    toggle_html = """
    <button class="mobile-menu-toggle" onclick="toggleSidebar()">
        ☰
    </button>
    <script>
    function toggleSidebar() {
        const sidebar = document.querySelector('.stSidebar');
        if (sidebar) {
            const isExpanded = sidebar.getAttribute('aria-expanded') !== 'false';
            sidebar.setAttribute('aria-expanded', !isExpanded);
        }
    }
    </script>
    """
    st.markdown(toggle_html, unsafe_allow_html=True)

def create_mobile_navigation():
    """Create mobile bottom navigation"""
    nav_html = """
    <div class="mobile-nav">
    """
    
    for item in MOBILE_NAV_ITEMS:
        nav_html += f"""
        <a href="#" class="mobile-nav-item" onclick="navigateTo('{item['page']}')">
            <div style="font-size: 20px;">{item['icon']}</div>
            <div style="font-size: 12px;">{item['label']}</div>
        </a>
        """
    
    nav_html += """
    </div>
    <script>
    function navigateTo(page) {
        // Handle navigation logic
        console.log('Navigate to:', page);
    }
    </script>
    """
    
    st.markdown(nav_html, unsafe_allow_html=True)

def create_touch_friendly_button(text: str, key: str = None, **kwargs):
    """Create a touch-friendly button"""
    return st.button(
        text, 
        key=key,
        use_container_width=True,
        **kwargs
    )

def create_mobile_chat_input(placeholder: str = "输入消息...", key: str = None):
    """Create mobile-optimized chat input"""
    return st.chat_input(
        placeholder,
        key=key
    )

def create_responsive_columns(sizes: list = [1, 1]):
    """Create responsive columns that adapt to screen size"""
    if len(sizes) == 2:
        return st.columns(sizes)
    elif len(sizes) == 3:
        return st.columns(sizes)
    else:
        return st.columns(len(sizes))

def create_mobile_sidebar():
    """Create mobile-optimized sidebar"""
    with st.sidebar:
        st.markdown("### 📱 移动端设置")
        
        # Mobile-specific settings
        st.checkbox("启用触觉反馈", value=True, key="haptic_feedback")
        st.checkbox("自动滚动", value=True, key="auto_scroll")
        st.checkbox("语音输入", value=False, key="voice_input")
        
        # Font size adjustment
        font_size = st.slider("字体大小", 12, 20, 16, key="font_size")
        
        # Theme selection for mobile
        theme = st.selectbox(
            "主题",
            ["浅色", "深色", "自动"],
            key="mobile_theme"
        )

def detect_mobile_device() -> bool:
    """Detect if user is on mobile device"""
    # This is a simple detection - in production, you'd use more sophisticated methods
    user_agent = st.get_option("browser.gatherUsageStats")
    return True  # For demo purposes, assume mobile

def create_mobile_optimized_chat():
    """Create mobile-optimized chat interface"""
    # Apply mobile optimizations
    apply_mobile_optimizations()
    
    # Create mobile header
    create_mobile_header()
    
    # Create mobile menu toggle
    create_mobile_menu_toggle()
    
    # Main chat area
    st.markdown('<div class="mobile-content">', unsafe_allow_html=True)
    
    # Chat messages
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Chat input
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    user_input = create_mobile_chat_input()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mobile navigation
    create_mobile_navigation()
    
    return user_input

def create_mobile_settings():
    """Create mobile-optimized settings page"""
    apply_mobile_optimizations()
    
    st.markdown("### ⚙️ 移动端设置")
    
    # Mobile-specific settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎨 显示设置")
        st.checkbox("深色模式", key="mobile_dark_mode")
        st.slider("字体大小", 12, 20, 16, key="mobile_font_size")
        st.selectbox("语言", ["中文", "English"], key="mobile_language")
    
    with col2:
        st.markdown("#### 🔊 音频设置")
        st.checkbox("语音输入", key="mobile_voice_input")
        st.checkbox("语音输出", key="mobile_voice_output")
        st.slider("音量", 0, 100, 50, key="mobile_volume")
    
    # Performance settings
    st.markdown("#### ⚡ 性能设置")
    st.checkbox("省电模式", key="mobile_power_save")
    st.checkbox("数据节省", key="mobile_data_save")
    st.selectbox("图像质量", ["低", "中", "高"], key="mobile_image_quality")

def create_mobile_analytics():
    """Create mobile-optimized analytics dashboard"""
    apply_mobile_optimizations()
    
    st.markdown("### 📊 使用统计")
    
    # Mobile-friendly charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("今日对话", "42", "↑ 12%")
        st.metric("活跃时间", "2.5h", "↑ 0.5h")
    
    with col2:
        st.metric("消息数量", "156", "↑ 23%")
        st.metric("满意度", "4.8/5", "↑ 0.2")

def export_mobile_config() -> Dict[str, Any]:
    """Export mobile configuration"""
    return {
        "haptic_feedback": st.session_state.get("haptic_feedback", True),
        "auto_scroll": st.session_state.get("auto_scroll", True),
        "voice_input": st.session_state.get("voice_input", False),
        "font_size": st.session_state.get("font_size", 16),
        "mobile_theme": st.session_state.get("mobile_theme", "自动"),
        "power_save": st.session_state.get("mobile_power_save", False),
        "data_save": st.session_state.get("mobile_data_save", False),
        "image_quality": st.session_state.get("mobile_image_quality", "中")
    }

def import_mobile_config(config: Dict[str, Any]):
    """Import mobile configuration"""
    for key, value in config.items():
        st.session_state[key] = value
