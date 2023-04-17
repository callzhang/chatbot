import streamlit as st, pandas as pd
from streamlit_chat import message
from tools import imagegen, asr, openai, utils, bing
import time, datetime, logging, json, re
# from streamlit_extras.colored_header import colored_header
from streamlit_extras.buy_me_a_coffee import button


# 初始化
if 'layout' not in st.session_state:
    st.session_state.layout = 'centered'
st.set_page_config(page_title="💬星尘小助手", page_icon="💬",
                   layout=st.session_state.layout, 
                   initial_sidebar_state="auto", menu_items={
             'Get Help': 'https://stardust.ai',
            #  'Report a bug': "https://www.extremelycoolapp.com/bug",
             'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
    })
st.title("💬星尘小助手")

## user auth
user_db = utils.get_db()
if 'name' not in st.session_state:
    st.session_state.guest = True
    st.warning('本系统需要消耗计算资源，特别是图片和语音功能；请适度体验AI的能力，尽量用在工作相关内容上😊')
    code = st.text_input('请输入你的访问码', help='仅限员工使用，请勿外传！')
    if code:
        access_data = user_db.query('访问码==@code')
        if len(access_data):
            st.session_state.name = access_data['姓名'].iloc[0]
            expiration = access_data['截止日期'].iloc[0]
            if datetime.datetime.now().date() < expiration:
                st.session_state.guest = False
        else:
            st.session_state.name = code
        st.experimental_rerun()
    st.stop()
    
## dialog history management
# history: 所有对话标题的索引，[time, title, file]
# conversation: 对话的具体内容列表，[{role, name, time, content, suggestion},...]
if "conversation" not in st.session_state:
    # 初始化当前对话
    chat_history = utils.get_dialog_history(st.session_state.name)
    # 初始化对话列表
    st.session_state.chat_titles = chat_history['title'].tolist()
    # 没有历史记录或创建新对话，增加“新对话”至title
    if not st.session_state.chat_titles:
        utils.new_dialog(st.session_state.name)
        st.experimental_rerun()
    elif 'new_chat' in st.session_state:
        selected_title = st.session_state.new_chat
        del st.session_state.new_chat
    elif 'chat_title_selection' in st.session_state:
        selected_title = st.session_state.chat_title_selection
    else:
        selected_title = st.session_state.chat_titles[0]
        
    # 初始化对话记录
    conversation = utils.get_conversation(st.session_state.name, selected_title)
    # update system prompt
    st.session_state.conversation = utils.system_prompt.copy()
    if st.session_state.guest:
        st.session_state.conversation += utils.guest_prompt(st.session_state.name)
    else:
        st.session_state.conversation += utils.staff_prompt(st.session_state.name)
    st.session_state.conversation += conversation
    

## UI
if st.session_state.guest:
    st.info('访客模式：支持最大10轮对话和20轮聊天历史')
    
# 聊天历史列表
def on_conversation_change():
    del st.session_state.conversation
selected_title = st.sidebar.radio('聊天历史', 
                                  st.session_state.chat_titles, 0, 
                                  key='chat_title_selection', 
                                  on_change=on_conversation_change)
# 对文本输入进行应答
def gen_response(query=None):
    # remove suggestion
    if 'suggestions' in st.session_state.conversation[-1]:
        st.session_state.conversation[-1].pop('suggestions')
    if 'action' in st.session_state.conversation[-1]:
        st.session_state.conversation[-1].pop('action')
        
    # get task and input
    task = st.session_state.task
    if task in ['对话', '文字做图', 'GPT-4', '文心一言']:
        user_input = query or st.session_state.input_text
        if user_input == '':
            return
        st.session_state.input_text = ""
    elif task == '语音识别':
        audio_file = st.session_state.get('audio')
        if audio_file:
            user_input = audio_file.name
    else:
        raise NotImplementedError(task)
    
    # gen user query
    print(f'{st.session_state.name}({task}): {user_input}')
    query_dict = {
        "role": "user",
        "name": st.session_state.name, 
        "content": user_input, 
        "task": task, 
        "time": datetime.datetime.now()
    }
    # display and update db
    st.session_state.conversation.append(query_dict)
    utils.update_conversation(st.session_state.name, selected_title, query_dict)
    
    # response
    if task == '对话':
        queue = openai.chat_stream(st.session_state.conversation, st.session_state.name)
        bot_response = {'role': 'assistant', 
                        'content': '', 
                        'queue': queue,
                        'time': datetime.datetime.now(),
                        'task': task,
                        'name': 'ChatGPT'
                        }
        chat = None
        st.session_state.conversation.append(bot_response)
    elif task == 'GPT-4':
        if 'bing' not in st.session_state:
            logging.warning('Initiating BingAI, please wait...')
            # show loading
            st.spinner('正在初始化BingAI')
            st.session_state.bing = bing.BingAI(name=st.session_state.name)
        
        queue, thread = st.session_state.bing.chat_stream(user_input)
        bot_response = {'role': 'assistant', 
                        'content': '', 
                        'queue': queue, 
                        'thread': thread,
                        'time': datetime.datetime.now(),
                        'name': 'BingAI'
                        }
        chat = None
        st.session_state.conversation.append(bot_response)
    elif task == '文字做图':
        with st.spinner('正在绘制'):
            urls_md = imagegen.gen_image(user_input)
            chat = {
                'role': 'assistant',
                'content': urls_md ,
                'task': task,
                'name': 'DALL·E',
                'time': datetime.datetime.now()
            }
            st.session_state.conversation.append(chat)
            utils.update_conversation(st.session_state.name, selected_title, chat)
            print(f'DALL·E: {chat}')
            print('-'*50)
    elif task == '语音识别':
        with st.spinner('正在识别'):
            st.session_state.conversation.append({
                'role': 'audio',
                'content': audio_file
            })
            transcription = asr.transcript(audio_file)
            chat = {
                'role': 'assistant',
                'content': chat,
                'task': task,
                'name': 'Whisper',
                'time': datetime.datetime.now()
            }
            st.session_state.conversation.append(chat)
            utils.update_conversation(st.session_state.name, selected_title, chat)
            print(f'Whisper: {transcription}')
            print('-'*50)
    else:
        raise NotImplementedError(task)


def handle_action(action_token):
    if action_token == utils.RETRY_TOKEN:
        bot_response = st.session_state.conversation.pop(-1)
        user_prompt = st.session_state.conversation.pop(-1)
        if bot_response['role'] == 'assistant' \
            and user_prompt['role'] == 'user':
            user_input = user_prompt['content']
            gen_response(query=user_input)
    else:
        raise NotImplementedError(action_token)


# 显示对话内容
def finish_reply(chat):
    if chat.get('thread'):
        chat['thread'].join()
        chat.pop('thread')
    chat.pop('queue')
    utils.update_conversation(st.session_state.name, selected_title, chat)
    
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
        queue = c.get('queue')
        if queue is not None:
            # 获取数据
            while len(queue):
                content = queue.popleft()
                if content == utils.FINISH_TOKEN:
                    finish_reply(c)
                    st.experimental_rerun()
                else:
                    c['content'] += content
                    c['time'] = datetime.datetime.now()
            # 超时
            if (datetime.datetime.now() - c['time']).total_seconds() > utils.TIMEOUT:
                c['content'] += '\n\n抱歉出了点问题，请重试...'
                c['actions'] = {'重试': utils.RETRY_TOKEN}
                finish_reply(c)
                
            # 渲染
            content = c['content'].replace(utils.SUGGESTION_TOKEN, '')
            message(content, key=str(i), avatar_style='jdenticon')
            time.sleep(0.3)
            st.experimental_rerun()
        else:
            # 结束
            content = c['content']
            suggestions = c.get('suggestions', [])
            # suggestion
            if not suggestions:
                content, suggestions = utils.parse_suggestions(content)
                c['content'] = content
                c['suggestions'] = suggestions
            message(content, key=str(i), avatar_style='jdenticon')
            # seggestions
            if suggestions and i == len(st.session_state.conversation) -1:
                cols = st.columns(len(suggestions))
                for col, suggestion in zip(cols, suggestions):
                    with col:
                        # if suggestion:
                            st.button('👉🏻'+suggestion[:50], help=suggestion,
                                      on_click=gen_response, kwargs={'query': suggestion})
            
            # actions: only "retry" is supported
            actions= c.get('actions')
            if actions and i == len(st.session_state.conversation) -1:
                if type(actions) is str:
                    actions = eval(actions)
                for action, token in actions.items():
                    st.button(action, on_click=handle_action, args=(token,))
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
    task = st.selectbox('选择功能', ['对话', 'GPT-4', '文字做图', '语音识别'], key='task', label_visibility='collapsed')
with c2:
    # guest limit
    if st.session_state.guest and len(st.session_state.conversation) > 10:
        disabled, help = True, '访客不支持长对话，请联系管理员'
    elif task == '对话':
        disabled, help = False, '输入你的问题，然后按回车提交。'
    elif task == '文心一言':
        disabled, help = True, '文心一言功能暂未开放'
    elif task == 'GPT-4':
        if utils.get_bingai_key(st.session_state.name) is None:
            disabled, help = True, '请先在设置中填写BingAI的秘钥'
        else:
            disabled, help = False, '输入你的问题，然后按回车提交给BingAI。'
    elif task == '文字做图':
        disabled, help = st.session_state.guest, '访客不支持文字做图'
    elif task == '语音识别':
        disabled, help = st.session_state.guest, '访客不支持语音识别'
    else:
        raise NotImplementedError(task)
    # 输入框
    if task in ['对话', '文字做图', 'GPT-4', '文心一言']:
        user_input = st.text_input(label="输入你的问题：", placeholder=help,
                            help=help,
                            max_chars=100 if st.session_state.guest else 000,
                            key='input_text', disabled=disabled,
                            label_visibility='collapsed',
                            on_change=gen_response)
    elif task == '语音识别':
        audio_file = st.file_uploader('上传语音文件', type=asr.accepted_types, key='audio', on_change=gen_response, disabled=disabled)
    else:
        raise NotImplementedError(task)

## 聊天历史功能区
c1, c2, c3, c4 = st.sidebar.columns(4)

with c1: # 新对话
    if st.session_state.guest and len(st.session_state.chat_titles) >= 20:
        disabled, help = True, '访客不支持超过10轮对话，请联系管理员'
    else:
        disabled, help = False, '新对话'
    if st.button('➕', key='clear', help=help, disabled=disabled):
        del st.session_state.conversation
        title = utils.new_dialog(st.session_state.name)
        st.session_state.new_chat = title
        st.session_state.audio = None
        st.session_state.layout = 'centered'
        st.experimental_rerun()
with c2: # 删除
    if st.button('⛔', help='删除当前聊天记录', disabled=st.session_state.guest):
        del st.session_state.conversation
        utils.delete_dialog(st.session_state.name, selected_title)
        st.experimental_rerun()
with c3: # 导出
    if st.download_button(label='📤', help='导出对话',
                        data=utils.conversation2markdown(st.session_state.conversation, st.session_state.name), 
                        file_name=f'history.md',
                        mime='text/markdown'):
        st.success('导出成功！')
        
with c4: # 修改
    def update_title():
        del st.session_state.conversation
        new_title = st.session_state.new_title_text
        utils.edit_dialog_name(st.session_state.name, selected_title, new_title)
        # st.experimental_rerun()
    if st.button('✏️', help='修改对话名称'):
        new_title = st.sidebar.text_input('修改名称', selected_title, help='修改当前对话标题', key='new_title_text', on_change=update_title)
        
        
# debug        
if st.session_state.name == "Derek":
    if st.button('👨‍💻', key='dev', help='开发者信息'):
        # st.markdown(st.session_state.conversation)
        pass
        
from streamlit_extras.add_vertical_space import add_vertical_space
add_vertical_space(20)
# buy me a coffee
button(username="derekz", floating=False, width=221)
