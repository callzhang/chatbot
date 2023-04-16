import streamlit as st
from tools import utils, convert_md_csv
import time

st.set_page_config(initial_sidebar_state="auto")

chat_per_page = 20

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()


# get history
chat_history = utils.get_chat_history(st.session_state.name)
chat_titles = chat_history['title']
if not len(chat_titles):
    st.info('暂无历史记录')
    st.stop()

# print(f'dates: {chat_history.keys()}')
# current_page = st.selectbox('选择日期', dates, 0)
selected_title = st.sidebar.radio('聊天历史', chat_titles.sort_values(ascending=False), 0)
# display chat in current page
chat_file = chat_history.query('title==@selected_title').iloc[0]['file']
chats = utils.get_conversation(chat_file)
chat_md = utils.render_markdown(chats, title=selected_title)
st.markdown(chat_md)
# export
st.download_button(label='📤', help='导出记录', data=chat_md, 
                   file_name=f'stardust_chatbot({selected_title}).md',
                   mime='text/markdown')

if st.session_state.name == "Derek":
    if st.button('convert'):
        convert_md_csv.convert_md_csv()
        st.balloons()