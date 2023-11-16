from st_pages import Page, show_pages, add_page_title
import streamlit as st

add_page_title()
pages = [
        Page("chatbot.py", "星尘小助手", "💬"),
        Page("pages/⭐️精选应用.py", "精选应用", ":star:"),
        # Section("My section", icon="🎈️"),
        Page("pages/📒聊天历史.py", icon="📒"),
        Page("pages/㊙️秘钥管理.py", icon="㊙️"),
    ]

if st.secrets.debug:
    pages.append(Page("pages/🤗助理.py", icon="🤗"))
show_pages(pages)