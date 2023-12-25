import streamlit as st
from tools import dialog, utils

st.set_page_config(initial_sidebar_state="auto")

chat_per_page = 20

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()


# get history
chat_history = dialog.get_dialog_history(st.session_state.name)
chat_titles = chat_history.col_values(2)[1:]
if not len(chat_titles):
    st.info('暂无历史记录')
    st.stop()

# print(f'dates: {chat_history.keys()}')
# current_page = st.selectbox('选择日期', dates, 0)
selected_title = st.sidebar.radio('聊天历史', chat_titles, 0)
# display chat in current page
chats = dialog.get_messages(st.session_state.name, selected_title)
if not chats:
    st.info('暂无历史记录')
    st.stop()
chat_md = dialog.conversation2markdown(chats, title=selected_title)
st.markdown(chat_md)
st.download_button('下载聊天记录', data=chat_md.encode('utf-8'), file_name=f'{selected_title}.md', mime='text/markdown')
