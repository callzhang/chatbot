"""
Theme management system for Stardust.ai Chatbot
Provides dark/light mode toggle and custom themes
"""

import streamlit as st
from typing import Dict, Any
import json

# Theme configurations
THEMES = {
    "light": {
        "primaryColor": "#FF6B6B",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#262730",
        "font": "sans serif"
    },
    "dark": {
        "primaryColor": "#FF6B6B",
        "backgroundColor": "#0E1117",
        "secondaryBackgroundColor": "#262730",
        "textColor": "#FAFAFA",
        "font": "sans serif"
    },
    "stardust": {
        "primaryColor": "#6366F1",
        "backgroundColor": "#0F0F23",
        "secondaryBackgroundColor": "#1A1A2E",
        "textColor": "#E2E8F0",
        "font": "sans serif"
    },
    "ocean": {
        "primaryColor": "#06B6D4",
        "backgroundColor": "#F0F9FF",
        "secondaryBackgroundColor": "#E0F2FE",
        "textColor": "#0C4A6E",
        "font": "sans serif"
    }
}

# CSS for additional theme customization
THEME_CSS = {
    "light": """
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 2rem;
        padding: 2rem;
    }
    .stChatMessage {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
    "dark": """
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    .main .block-container {
        background-color: rgba(14, 17, 23, 0.95);
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-top: 2rem;
        padding: 2rem;
    }
    .stChatMessage {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background-color: #262730;
        color: #FAFAFA;
    }
    </style>
    """,
    "stardust": """
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main .block-container {
        background-color: rgba(15, 15, 35, 0.95);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
        margin-top: 2rem;
        padding: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .stChatMessage {
        background-color: #1A1A2E;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(99, 102, 241, 0.1);
    }
    .theme-toggle {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
    }
    </style>
    """,
    "ocean": """
    <style>
    .stApp {
        background: linear-gradient(135deg, #06B6D4 0%, #0891B2 100%);
    }
    .main .block-container {
        background-color: rgba(240, 249, 255, 0.95);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2);
        margin-top: 2rem;
        padding: 2rem;
        border: 1px solid rgba(6, 182, 212, 0.1);
    }
    .stChatMessage {
        background-color: #E0F2FE;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(6, 182, 212, 0.1);
    }
    </style>
    """
}

def initialize_theme():
    """Initialize theme in session state"""
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    if 'theme_config' not in st.session_state:
        st.session_state.theme_config = THEMES['light']

def get_current_theme() -> str:
    """Get current theme name"""
    initialize_theme()
    return st.session_state.theme

def set_theme(theme_name: str):
    """Set theme by name"""
    if theme_name in THEMES:
        st.session_state.theme = theme_name
        st.session_state.theme_config = THEMES[theme_name]
        return True
    return False

def get_theme_config(theme_name: str = None) -> Dict[str, Any]:
    """Get theme configuration"""
    if theme_name is None:
        theme_name = get_current_theme()
    return THEMES.get(theme_name, THEMES['light'])

def apply_theme_css(theme_name: str = None):
    """Apply theme CSS"""
    if theme_name is None:
        theme_name = get_current_theme()
    
    css = THEME_CSS.get(theme_name, THEME_CSS['light'])
    st.markdown(css, unsafe_allow_html=True)

def create_theme_selector():
    """Create theme selector component"""
    initialize_theme()
    
    # Theme selector in sidebar
    with st.sidebar:
        st.markdown("### 🎨 主题设置")
        
        # Theme selection
        theme_options = {
            "☀️ 浅色模式": "light",
            "🌙 深色模式": "dark", 
            "✨ 星尘主题": "stardust",
            "🌊 海洋主题": "ocean"
        }
        
        selected_theme_display = st.selectbox(
            "选择主题",
            options=list(theme_options.keys()),
            index=list(theme_options.values()).index(st.session_state.theme),
            key="theme_selector"
        )
        
        selected_theme = theme_options[selected_theme_display]
        
        if selected_theme != st.session_state.theme:
            set_theme(selected_theme)
            st.rerun()
        
        # Theme preview
        st.markdown("#### 主题预览")
        theme_config = get_theme_config()
        
        col1, col2 = st.columns(2)
        with col1:
            st.color_picker("主色调", value=theme_config['primaryColor'], disabled=True)
        with col2:
            st.color_picker("背景色", value=theme_config['backgroundColor'], disabled=True)

def create_theme_toggle_button():
    """Create a floating theme toggle button"""
    initialize_theme()
    
    # JavaScript for theme toggle
    toggle_js = """
    <script>
    function toggleTheme() {
        const currentTheme = localStorage.getItem('stardust-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('stardust-theme', newTheme);
        window.location.reload();
    }
    </script>
    """
    
    # Toggle button HTML
    toggle_html = f"""
    <div class="theme-toggle">
        <button onclick="toggleTheme()" style="
            background: {'#FF6B6B' if st.session_state.theme == 'light' else '#6366F1'};
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        ">
            {'🌙' if st.session_state.theme == 'light' else '☀️'}
        </button>
    </div>
    """
    
    st.markdown(toggle_js + toggle_html, unsafe_allow_html=True)

def save_theme_preference(theme_name: str):
    """Save theme preference to local storage"""
    # This would typically be saved to a database or user preferences
    # For now, we'll use session state
    st.session_state.theme = theme_name

def load_theme_preference() -> str:
    """Load theme preference from storage"""
    # This would typically load from a database or user preferences
    # For now, we'll use session state
    return st.session_state.get('theme', 'light')

def get_theme_icon(theme_name: str) -> str:
    """Get icon for theme"""
    icons = {
        'light': '☀️',
        'dark': '🌙',
        'stardust': '✨',
        'ocean': '🌊'
    }
    return icons.get(theme_name, '🎨')

def export_theme_config(theme_name: str = None) -> str:
    """Export theme configuration as JSON"""
    if theme_name is None:
        theme_name = get_current_theme()
    
    config = get_theme_config(theme_name)
    return json.dumps(config, indent=2)

def import_theme_config(config_json: str) -> bool:
    """Import theme configuration from JSON"""
    try:
        config = json.loads(config_json)
        # Validate required keys
        required_keys = ['primaryColor', 'backgroundColor', 'secondaryBackgroundColor', 'textColor']
        if all(key in config for key in required_keys):
            # Add to themes (this would typically be saved to a database)
            theme_name = f"custom_{len(THEMES)}"
            THEMES[theme_name] = config
            return True
    except json.JSONDecodeError:
        pass
    return False
