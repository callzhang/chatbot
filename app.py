"""
Stardust.ai Chatbot - Main Application Entry Point
Optimized for cloud deployment platforms
"""

import os
import sys
import streamlit as st

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config for cloud deployment
st.set_page_config(
    page_title="🌟 星尘小助手 - Stardust.ai Chatbot",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-username/chatbot',
        'About': "# 星尘小助手\n一个功能丰富的AI聊天助手，集成了多种AI模型和实用工具"
    }
)

# Import and run the main application
if __name__ == "__main__":
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        st.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        st.info("请在部署平台设置以下环境变量:")
        for var in missing_vars:
            st.code(f"{var}=your-api-key-here")
        st.stop()
    
    # Run the main application
    try:
        from home import *
    except ImportError as e:
        st.error(f"❌ 导入错误: {e}")
        st.info("请确保所有依赖都已正确安装")
        st.stop()
    except Exception as e:
        st.error(f"❌ 应用启动错误: {e}")
        st.info("请检查配置和依赖")
        st.stop()
