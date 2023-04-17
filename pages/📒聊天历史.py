import streamlit as st
from tools import utils, convert_md_csv
import time

st.set_page_config(initial_sidebar_state="auto")

chat_per_page = 20

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()

# 特殊功能
if st.session_state.name == "Derek":
    if st.button('convert'):
        zipfile = convert_md_csv.convert_md_csv()
        with open(zipfile, 'rb') as f:
            bytes = f.read()
            st.download_button('download zip', data=bytes, file_name='chats.zip')
            st.balloons()

# get history
chat_history = utils.get_dialog_history(st.session_state.name)
chat_titles = chat_history['title']
if not len(chat_titles):
    st.info('暂无历史记录')
    st.stop()

# print(f'dates: {chat_history.keys()}')
# current_page = st.selectbox('选择日期', dates, 0)
selected_title = st.sidebar.radio('聊天历史', chat_titles, 0)
# display chat in current page
chats = utils.get_conversation(st.session_state.name, selected_title)
if not chats:
    st.info('暂无历史记录')
    st.stop()
chat_md = utils.conversation2markdown(chats, title=selected_title)
st.markdown(chat_md)
