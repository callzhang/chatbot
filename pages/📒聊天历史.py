import streamlit as st, os, re, datetime
from collections import defaultdict

chat_per_page = 20

if 'name' not in st.session_state:
    st.info('请先登录')
    st.stop()

# cached function to get history
@st.cache(ttl=600)  # update every 10 minute
def get_history(history_file):
    if os.path.exists(history_file):
        with open(f'chats/{st.session_state.name}.md', 'r') as f:
            chat_log = f.read()
    else:
        chat_log = ''
        
    # find all occurance of '---' and split the string
    chat_splited = re.split(r'---+', chat_log)
    patten = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]" #r"\d{4}-\d{2}-\d{2}"
    chat_history = defaultdict(list)
    for chat in chat_splited:
        datetime_str = re.findall(patten, chat)
        if datetime_str:
            t = datetime.datetime.strptime(datetime_str[0][1:-1], '%Y-%m-%d %H:%M:%S')
            date_str = t.strftime('%Y-%m-%d')
            chat_history[date_str].append(chat)
        elif chat.strip():
            chat_history['无日期'].append(chat)
    return chat_history

# get data
history_file = f'chats/{st.session_state.name}.md'
chat_history = get_history(history_file)
dates = sorted(chat_history, reverse=True)
if not chat_history:
    st.info('暂无历史记录')
    st.stop()

print(f'dates: {chat_history.keys()}')
current_page = st.selectbox('选择日期', dates, 0)
print(f'selected {current_page}')
# display chat in current page
chats = chat_history[current_page]
chat_md = '\n---\n'.join(chats)
st.markdown(chat_md)
# export
st.download_button(label='📤', help='导出记录', data=chat_md, 
                   file_name=f'stardust_chatbot({current_page}).md',
                   mime='text/markdown')
