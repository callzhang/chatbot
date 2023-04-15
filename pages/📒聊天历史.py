import streamlit as st
from tools import utils
import time

st.set_page_config(initial_sidebar_state="auto")

chat_per_page = 20

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()


# get data
chat_history = utils.get_history(st.session_state.name)
dates = sorted(chat_history, reverse=True)
if not chat_history:
    st.info('暂无历史记录')
    st.stop()

# print(f'dates: {chat_history.keys()}')
# current_page = st.selectbox('选择日期', dates, 0)
current_page = st.sidebar.radio('选择对话', dates, 0)
# display chat in current page
chats = chat_history[current_page]
chat_md = '\n---\n'.join(chats)
st.markdown(chat_md)
# export
st.download_button(label='📤', help='导出记录', data=chat_md, 
                   file_name=f'stardust_chatbot({current_page}).md',
                   mime='text/markdown')

if st.session_state.name == "Derek":
    # st.button('convert history')
    if st.button('download md'):
        filename = 'chats.zip'
        zipfile = utils.zip_folder('chats', filename)
        with open(zipfile, 'rb') as f:
            st.download_button('download', data=f.read(), file_name=filename)