import streamlit as st
from streamlit_chat import message
from utils import chat, imagegen, asr
import pandas as pd
import time
# from streamlit_extras.colored_header import colored_header
from streamlit_extras.buy_me_a_coffee import button

WIDE_LAYOUT_THRESHOLD = 400

# 初始化
st.session_state.guest = True
if 'layout' not in st.session_state:
    st.session_state.layout = 'centered'
st.set_page_config(page_title="星尘小助手", page_icon=":star:", 
                   layout=st.session_state.layout, 
                   initial_sidebar_state="collapsed", menu_items={
             'Get Help': 'https://stardust.ai',
            #  'Report a bug': "https://www.extremelycoolapp.com/bug",
             'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
    })
st.title("🪐星尘小助手")

# 名字
with open('names.txt', 'r') as f:
    names = [n.strip() for n in f.readlines()]

if 'name' not in st.session_state:
    st.warning('本系统需要消耗计算资源，特别是图片和语音功能；请适度体验AI的能力，尽量用在工作相关内容上😊')
    name = st.text_input('请输入你的名字', key='my_name', help='仅限员工使用，请勿外传！')
    if name:
        st.session_state.name = name
        st.experimental_rerun()
    st.stop()

if st.session_state.name in names:
    st.session_state.guest = False
    

# 定义一个列表，用于保存对话内容。role：system，user，assistant
if "conversation" not in st.session_state:
    st.session_state.conversation = chat.init_prompt.copy()
    if st.session_state.guest:
        st.session_state.conversation.append(
            chat.guest_prompt(st.session_state.name))
    else:
        st.session_state.conversation.append(chat.staff_prompt)

## UI
# 对文本输入进行应答
def gen_response():
    task = st.session_state.task
    if task in ['对话', '作图']:
        user_input = st.session_state.input_text
        if user_input == '':
            return
        st.session_state.input_text = ""
    elif task == '语音识别':
        audio_file = st.session_state.audio
        if audio_file is None:
            return
        user_input = audio_file.name
        
    print(f'{st.session_state.name}({task}): {user_input}')
    st.session_state.conversation.append({"role": "user", "content": user_input})
    # guest 超长对话
    if st.session_state.guest and len(st.session_state.conversation) > 10:
        st.session_state.conversation.append({"role": "assistant", "content": '访客不支持长对话，请联系管理员'})
        return
    # response
    if task == '对话':
        # with st.spinner('正在思考'):
            # response = bot_response["content"]
            # print(f'星尘小助手: {response}')
            # print('-'*50)
        queue = chat.chat_stream(st.session_state.conversation)
        bot_response = {'role': 'assistant', 'content': '', 'queue': queue, 'active': True}
        response = ''
        st.session_state.conversation.append(bot_response)
    elif task == '作图':
        with st.spinner('正在绘制'):
            urls = imagegen.gen_image(user_input)
            response = urls
            st.session_state.conversation.append({
                'role': 'imagen',
                'content': urls 
            })
            print(f'Imagen: {response}')
            print('-'*50)
    elif task == '语音识别':
        with st.spinner('正在识别'):
            response = asr.transcript(audio_file)
            st.session_state.conversation.append({
                'role': 'audio',
                'content': audio_file
            })
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': response 
            })
            print(f'Whisper: {response}')
            print('-'*50)
    else:
        raise NotImplementedError(task)
    # log
    with open(f'chats/{st.session_state.name}.txt', 'a') as f:
        f.write(f'{st.session_state.name}: {user_input}\n')
        f.write(f'星尘小助手({task}): {response}\n')
        f.write('-'*50 + '\n')


# 显示对话内容
md_formated = ""
for i, c in enumerate(st.session_state.conversation):
    role, content = c['role'], c['content']
    if role == "system":
        continue
    elif role == 'server':# not implemented
        message(content, is_user=False, key=str(i))
    elif role == "user":
        message(content, is_user=True, key=str(i),
                avatar_style='initials', seed=st.session_state.name[-2:])
    elif role == "assistant":
        if c.get('active'):
            queue = c['queue']
            text = ''
            stop = False
            while True:
                content = queue.get()
                if content == chat.finish_token:
                    c.pop('active')
                    c.pop('queue')
                    queue.close()
                    break
                elif not content:
                    break
                else:
                    text += content
            
            c['content'] += text
            message(c['content'], key=str(i), avatar_style='jdenticon')
            time.sleep(0.1)
            st.experimental_rerun()
        else:
            message(c['content'], key=str(i), avatar_style='jdenticon')

    elif role == 'imagen':
        n = len(content)
        cols = st.columns(n)
        for i, col, url in zip(range(1, n+1), cols, content):
            with col:
                st.image(url, use_column_width=True, caption=f'图{i+1}')
    elif role == 'audio':
        c1, c2 = st.columns([0.6,0.4])
        with c2:
            st.audio(content)
    else:
        raise Exception(c)

    # page layout
    if st.session_state.layout != 'wide' and len(c['content']) > WIDE_LAYOUT_THRESHOLD:
        st.session_state.layout = 'wide'
        st.experimental_rerun()

# 添加文本输入框
c1, c2 = st.columns([0.15,0.85])
with c1:
    task = st.selectbox('选择功能', ['对话', '作图', '语音识别'], key='task')
with c2:
    if task in ['对话', '作图']:
        user_input = st.text_input(label="输入你的问题：", placeholder='输入你的问题，然后按回车提交。',
                            help='输入你的问题，然后按回车提交。', 
                            max_chars=500,
                            key='input_text',
                            # label_visibility='collapsed',
                            on_change=gen_response)
    elif task == '语音识别':
        audio_file = st.file_uploader('上传语音文件', type=asr.accepted_types, key='audio', on_change=gen_response)




## 功能区
c1, c2, c3 = st.columns([0.1, 0.1, 0.8])
# 清空对话
with c1:
    if st.button('🧹', key='clear'):
        st.session_state.conversation = chat.init_prompt.copy()
        # st.session_state.input_text = ""
        st.session_state.audio = None
        # st.session_state.task = '对话'
        st.session_state.layout = 'centered'
        st.experimental_rerun()
with c2:
    # 导出对话内容
    def convert_history(conversation):
        history = pd.DataFrame(conversation).query('role not in ["system", "audio"]')
        return history.to_csv().encode('utf-8')
    if st.download_button(label='📤', help='导出对话内容',
                        data=convert_history(st.session_state.conversation), 
                        file_name=f'history.csv', 
                        mime='text/csv'):
        st.success('导出成功！')
        
from streamlit_extras.add_vertical_space import add_vertical_space
add_vertical_space(20)
# buy me a coffee
button(username="derekz", floating=False, width=221)
