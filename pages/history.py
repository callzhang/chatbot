import streamlit as st, os

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()

history_file = f'chats/{st.session_state.name}.md'
if os.path.exists(history_file):
    with open(f'chats/{st.session_state.name}.md', 'r') as f:
        chat_history = f.read()
        
    st.markdown(chat_history)
else:
    st.info('暂无历史记录')