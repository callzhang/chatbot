import streamlit as st
from streamlit_chat import message
from utils import chat, imagegen, asr
import pandas as pd

if 'layout' not in st.session_state:
    st.session_state.layout = 'centered'
# 设置页面标题
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
name_pl = st.empty()
if 'my_name' not in st.session_state:
    if 'name' in st.session_state and st.session_state.name != '':
        st.session_state.my_name = st.session_state.name
    else:
        st.warning('本系统需要消耗计算资源，特别是图片和语音功能；请适度体验AI的能力，尽量用在工作相关内容上😊')
        st.session_state.name = name_pl.text_input('请输入你的名字', key='my_name', help='仅限员工使用，请勿外传！')
else:
    st.session_state.name = st.session_state.my_name
if st.session_state.name == '':
    st.stop()
elif st.session_state.name not in names:
    st.warning('请输入正确的名字以使用本系统')
    st.stop()
else:
    name_pl.empty()
    

# 定义一个列表，用于保存对话内容。role：system，user，assistant
if "conversation" not in st.session_state:
    st.session_state.conversation = chat.init_prompt.copy()

## 功能函数
def get_chat_response():
    message = chat.chat(st.session_state.conversation)
    return message


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
    if task == '对话':
        with st.spinner('正在思考'):
            bot_response = get_chat_response()
            response = bot_response["content"]
            print(f'星尘小助手: {response}')
            print('-'*50)
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
    # page layout
    if len(response)>100:
        st.session_state.layout = 'wide'
    # log
    with open(f'chats/{st.session_state.name}.txt', 'a') as f:
        f.write(f'{st.session_state.name}: {user_input}\n')
        f.write(f'星尘小助手({task}): {response}\n')
        f.write('-'*50 + '\n')


# 显示对话内容
md_formated = ""
for i, c in enumerate(st.session_state.conversation):
    if c['role'] == "system":
        pass
    elif c['role'] == "user":
        message(c['content'], is_user=True, key=str(i),
                avatar_style='initials', seed=st.session_state.name[-2:])
    elif c['role'] == "assistant":
        message(c['content'], key=str(i), avatar_style='jdenticon')
        # 富文本
        if chat.is_markdown(c['content']):
            c0, c1, c2 = st.columns([0.05,0.7,0.25])
            with c1:
                with st.expander('查看富文本结果', expanded=False):
                    st.markdown(c['content'])
    elif c['role'] == 'imagen':
        n = len(c['content'])
        cols = st.columns(n)
        for i, col, url in zip(range(1, n+1), cols, c['content']):
            with col:
                st.image(url, use_column_width=True, caption=f'图{i+1}')
    elif c['role'] == 'audio':
        c1, c2 = st.columns([0.6,0.4])
        with c2:
            st.audio(c['content'])
    else:
        raise Exception(c)
# 添加文本输入框
c1, c2 = st.columns([0.15,0.85])
with c1:
    task = st.selectbox('选择功能', ['对话', '作图', '语音识别'], key='task', label_visibility='collapsed')
with c2:
    if task in ['对话', '作图']:
        user_input = st.text_input("输入你的问题：", 
                            help='输入你的问题，然后按回车提交。', 
                            max_chars=500,
                            key='input_text',
                            label_visibility='collapsed',
                            on_change=gen_response)
    elif task == '语音识别':
        audio_file = st.file_uploader('上传语音文件', type=asr.accepted_types, key='audio', label_visibility='collapsed', on_change=gen_response)
        
# 导出对话内容
history = pd.DataFrame(st.session_state.conversation).query('role not in ["system", "audio"]')
if len(history)>0 and st.download_button(label='📤', help='导出对话内容',
                      data=history.to_csv().encode('utf-8'), 
                      file_name=f'{st.session_state.name}.csv', 
                      mime='text/csv'):
    st.success('导出成功！')