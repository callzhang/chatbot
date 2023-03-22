import streamlit as st
from streamlit_chat import message
from tools import chat, imagegen, asr, utils, bing
import pandas as pd
import time, datetime, logging
# from streamlit_extras.colored_header import colored_header
from streamlit_extras.buy_me_a_coffee import button


# 初始化
st.session_state.guest = True
if 'layout' not in st.session_state:
    st.session_state.layout = 'centered'
st.set_page_config(page_title="💬星尘小助手", page_icon="💬",
                   layout=st.session_state.layout, 
                   initial_sidebar_state="collapsed", menu_items={
             'Get Help': 'https://stardust.ai',
            #  'Report a bug': "https://www.extremelycoolapp.com/bug",
             'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
    })
st.title("💬星尘小助手")

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
    st.session_state.conversation = utils.init_prompt.copy()
    if st.session_state.guest:
        st.session_state.conversation += utils.guest_prompt(st.session_state.name)
    else:
        st.session_state.conversation += utils.staff_prompt(st.session_state.name)
    
## UI
# 对文本输入进行应答
def gen_response():
    task = st.session_state.task
    if task in ['对话', '文字做图', '信息检索', '文星一言']:
        user_input = st.session_state.input_text
        if user_input == '':
            return
        st.session_state.input_text = ""
    elif task == '语音识别':
        audio_file = st.session_state.get('audio')
        if audio_file:
            user_input = audio_file.name
    else:
        raise NotImplementedError(task)
        
    print(f'{st.session_state.name}({task}): {user_input}')
    st.session_state.conversation.append({"role": "user", "content": user_input, "task": task})
    
    # guest 长对话处理
    if st.session_state.guest and len(st.session_state.conversation) > 10:
        st.session_state.conversation.append({"role": "assistant", "content": '访客不支持长对话，请联系管理员'})
        return
    
    # response
    if task == '对话':
        queue, thread = chat.chat_stream(st.session_state.conversation)
        bot_response = {'role': 'assistant', 
                        'content': '', 
                        'queue': queue, 
                        'thread': thread,
                        'start': time.time(),
                        'model': 'ChatGPT'
                        }
        response = None
        st.session_state.conversation.append(bot_response)
    elif task == '信息检索':
        if 'bing' not in st.session_state:
            logging.warning('Initiating BingAI, please wait...')
            # show loading
            st.spinner('正在初始化BingAI')
            st.session_state.bing = bing.BingAI()
        
        queue, thread = st.session_state.bing.chat_stream(user_input)
        bot_response = {'role': 'assistant', 
                        'content': '', 
                        'queue': queue, 
                        'thread': thread,
                        'start': time.time(),
                        'model': 'BingAI'
                        }
        response = None
        st.session_state.conversation.append(bot_response)
    elif task == '文字做图':
        with st.spinner('正在绘制'):
            urls = imagegen.gen_image(user_input)
            response = urls
            st.session_state.conversation.append({
                'role': 'DALL·E',
                'content': urls ,
                'model': 'DALL·E'
            })
            print(f'DALL·E: {response}')
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
                'content': response,
                'model': 'Whisper'
            })
            print(f'Whisper: {response}')
            print('-'*50)
    else:
        raise NotImplementedError(task)
    # log
    with open(f'chats/{st.session_state.name}.md', 'a') as f:
        tstring = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'**[{tstring}] {st.session_state.name}（{task}）: {user_input.strip()}**\n\n')
        if response:
            f.write(f'星尘小助手({task}): {response}\n')
            f.write('-'*50 + '\n')


# 显示对话内容
def finish_reply(chat):
    t0 = time.time()
    if chat['thread']:
        chat['thread'].join()
    logging.info(f'finish reply in {time.time() - t0:.2f}s')
    chat.pop('queue')
    chat.pop('start')
    chat.pop('thread')
    with open(f'chats/{st.session_state.name}.md', 'a') as f:
        response = c['content']
        f.write(f'星尘小助手（{c.get("model")}）: {response}\n\n---\n\n')
    
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
        if c.get('start'):
            queue, thread = c['queue'], c['thread']
            # 超时
            if time.time() - c['start'] > 30:
                c['content'] += '\n\n抱歉出了点问题，请重试...'
                finish_reply(c)
            # 获取数据
            while len(queue):
                content = queue.popleft()
                if content == chat.finish_token:
                    print('finish token received')
                    finish_reply(c)
                    break
                else:
                    c['content'] += content
                    c['start'] = time.time()
                    
            # 渲染
            message(c['content'], key=str(i), avatar_style='jdenticon')
            time.sleep(0.3)
            st.experimental_rerun()
        else:
            message(c['content'], key=str(i), avatar_style='jdenticon')

    elif role == 'DALL·E':
        message(c['content'], key=str(i), avatar_style='jdenticon')
    elif role == 'audio':
        c1, c2 = st.columns([0.6,0.4])
        with c2:
            st.audio(content)
    else:
        raise Exception(c)

    # page layout
    if st.session_state.layout != 'wide' and c['role']=='assistant' and len(c['content']) > utils.WIDE_LAYOUT_THRESHOLD:
        st.session_state.layout = 'wide'
        st.experimental_rerun()

# 添加文本输入框
c1, c2 = st.columns([0.18,0.82])
with c1:
    task = st.selectbox('选择功能', ['对话', '信息检索', '文星一言', '文字做图', '语音识别'], key='task', disabled=st.session_state.guest)
with c2:
    disabled, help = False, '输入你的问题，然后按回车提交。'
    if task == '文星一言':
        disabled, help = True, '文星一言功能暂未开放'
    elif task == '信息检索' and utils.get_bingai_key() is None:
        disabled, help = True, '请先在设置中填写BingAI的秘钥'
    
    if task in ['对话', '文字做图', '信息检索', '文星一言']:
        user_input = st.text_input(label="输入你的问题：", placeholder=help,
                            help=help,
                            max_chars=100 if st.session_state.guest else 000,
                            key='input_text', disabled=disabled,
                            # label_visibility='collapsed',
                            on_change=gen_response)
    elif task == '语音识别':
        audio_file = st.file_uploader('上传语音文件', type=asr.accepted_types, key='audio', on_change=gen_response)
    else:
        raise NotImplementedError(task)

## 功能区
c1, c2, c3 = st.columns([0.08, 0.08, 0.9])
# 清空对话
with c1:
    if st.button('🧹', key='clear', help='清空对话'):
        st.session_state.conversation = utils.init_prompt.copy()
        # st.session_state.input_text = ""
        st.session_state.audio = None
        # st.session_state.task = '对话'
        st.session_state.layout = 'centered'
        st.experimental_rerun()
with c2:
    if st.download_button(label='📤', help='导出对话',
                        data=utils.convert_history(st.session_state.conversation), 
                        file_name=f'history.md',
                        mime='text/markdown'):
        st.success('导出成功！')
with c3:
    if st.session_state.name == "Derek":
        if st.button('👨‍💻', key='dev', help='开发者信息'):
            st.markdown(st.session_state.conversation)
        
from streamlit_extras.add_vertical_space import add_vertical_space
add_vertical_space(20)
# buy me a coffee
button(username="derekz", floating=False, width=221)
