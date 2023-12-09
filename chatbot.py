import streamlit as st
# from streamlit_chat import message
from tools import dialog, utils, controller, model, auth, speech
from datetime import datetime, timedelta
# from streamlit_extras.colored_header import colored_header
from streamlit_extras.buy_me_a_coffee import button
import extra_streamlit_components as stx
import sys
runner = sys.modules["streamlit.runtime.scriptrunner.script_runner"]

# 初始化
Task = model.Task
Role = model.Role
Message = model.AppMessage
WIDE_LAYOUT_THRESHOLD = 1000
st.set_page_config(page_title="💬星尘小助手", page_icon="💬",
                   layout=st.session_state.desired_layout,
                   initial_sidebar_state="auto", menu_items={
             'Get Help': 'https://stardust.ai',
            #  'Report a bug': "https://www.extremelycoolapp.com/bug",
             'About': "# 星尘小助手. \n *仅限员工使用，请勿外传!*"
    })
if 'desired_layout' not in st.session_state:
    st.session_state.desired_layout = 'centered'
st.title("💬星尘小助手") 
    
# user auth
if 'name' not in st.session_state:
    st.session_state.guest = True
    cm = stx.CookieManager()
    code = cm.get(model.LOGIN_CODE)
    
    # 通知
    with open('README.md', 'r') as f:
        readme = f.read()
        st.toast(readme, icon='😍')
        
    # 登录
    if not code:
        st.info('我是一个集成多个聊天机器人能力的小助手，希望能帮助你提高工作效率😊')
        code = st.text_input('请输入你的访问码', help='仅限员工使用，请勿外传！')
    if code:
        user_db = auth.get_db()
        access_data = user_db.query('访问码==@code')
        exp_date = datetime.now() + timedelta(days=10)# set cookie expire date to 10 days later
        if len(access_data):
            st.session_state.name = access_data.index.values[0]
            expiration = access_data['截止日期'].iloc[0]
            if datetime.now().date() < expiration.date():
                # login success
                st.session_state.guest = False
                exp_date = datetime(expiration.year, expiration.month, expiration.day, 23, 59, 59)
        else: #guest
            st.session_state.name = code
        cm.set(model.LOGIN_CODE, code, expires_at=exp_date)
        st.rerun()
    st.stop()
    
## dialog history management
dialog.init_dialog(st.session_state.name)

##---- UI -----
task = st.selectbox('选择功能', Task.values(), key='task', label_visibility='collapsed')
# 聊天历史列表
def on_conversation_change():
    del st.session_state.conversation
    
st.session_state.selected_title = st.sidebar.radio('聊天历史', 
                                  st.session_state.dialog_history, 0, 
                                  key='chat_title_selection', 
                                  on_change=on_conversation_change)

if st.session_state.guest:
    st.info('访客模式：支持最大10轮对话和20轮聊天历史')

# 添加文本输入框
disabled = st.session_state.guest
if st.session_state.guest and len(st.session_state.conversation) > 10:
    disabled, help = True, '访客不支持长对话，请联系管理员'
elif task == Task.ChatGPT.value:
    disabled, help = False, '输入你的问题，然后按回车提交。'
elif task == Task.ChatSearch.value:
    help = '输入你的问题，如果信息需要检索，会自动调用搜索引擎。'
elif task == Task.GPT4.value:
    help = '输入你的问题，然后按回车提交。'
elif task == Task.GPT4V.value:
    help = '输入你的问题，并上传图片，然后按回车提交。'
elif task == Task.BingAI.value:
    if utils.get_bingai_key(st.session_state.name) is None:
        disabled, help = True, '请先在设置中填写BingAI的秘钥'
    else:
        disabled, help = False, '输入你的问题，然后按回车提交给BingAI。'
elif task == Task.text2img.value:
    help = '访客不支持文字做图' if st.session_state.guest else '输入你的prompt'
elif task == Task.ASR.value:
    help = '访客不支持语音识别' if st.session_state.guest else '上传语音文件'
elif task == Task.TTS.value:
    help = '访客不支持文本朗读' if st.session_state.guest else '输入需要朗读的文本'
else:
    raise NotImplementedError(task)

# 输入框
label = None
max_chars = controller.task_params[task][task]['max_tokens']
if task in Task.ASR.value:
    label = '🎤上传语音文件'
    filetypes = controller.speech_media_types
elif task == Task.GPT4V.value:
    label = '🎨上传图片'
    filetypes = controller.openai_image_types
if label:
    attachment = st.file_uploader(
        label, type=filetypes, key='attachment', disabled=disabled)
# input
user_input = st.chat_input(placeholder=help,
                           key='input_text',
                           disabled=disabled,
                           max_chars=max_chars,
                        #    on_submit=controller.gen_response
                           )
if user_input:
    user_message, bot_response = controller.gen_response(user_input)
    
# 显示对话内容
for i, message in enumerate(st.session_state.conversation):
    role, content, medias =  message.role, message.content, message.medias
    if role == Role.system.name:
        pass
    elif role == Role.server.name:# not implemented
        with st.chat_message(role):
            st.markdown(content)
    elif role == Role.user.name:
        if content or medias:
            with st.chat_message(role):
                if medias:
                    for media in medias:
                        controller.display_media(media)
                if content:
                    st.markdown(content)
    elif role == Role.assistant.name:
        message_placeholder =  st.chat_message(role)
        controller.show_streaming_message(message, message_placeholder)
        # append tts action
        if not st.session_state.guest and i == len(st.session_state.conversation)-1 and content:
            if message_placeholder.button('▶️'):
                st.toast('▶️正在转译语音')
                f = speech.text_to_speech(message.content)
                controller.play_audio(f, message_placeholder)
    else:
        raise Exception(f'Unknown role: {role}')

    # page layout
    if st.session_state.desired_layout != 'wide' and message.role=='assistant' and utils.token_size(message.content) > WIDE_LAYOUT_THRESHOLD:
        st.session_state.desired_layout = 'wide'
        st.rerun()


## 聊天历史功能区
c1, c2, c3, c4 = st.sidebar.columns(4)
with c1: # 新对话
    if st.session_state.guest and len(st.session_state.dialog_history) >= 20:
        disabled, help = True, '访客不支持超过10轮对话，请联系管理员'
    else:
        disabled, help = False, '新对话'
    if st.button('➕', help=help, disabled=disabled):
        del st.session_state.conversation
        title = dialog.new_dialog(st.session_state.name)
        st.session_state.new_title = title
        st.session_state.audio = None
        st.rerun()
with c2: # 删除
    if st.button('⛔', help='删除当前聊天记录', disabled=st.session_state.guest):
        del st.session_state.conversation
        dialog.delete_dialog(st.session_state.name, st.session_state.selected_title)
        st.rerun()
with c3: # 导出
    if st.download_button(label='📤', help='导出对话',
                        data=dialog.conversation2markdown(st.session_state.conversation, st.session_state.name), 
                        file_name=f'history.md',
                        mime='text/markdown'):
        st.success('导出成功！')
with c4: # 修改
    def update_title():
        del st.session_state.conversation
        new_title = st.session_state.new_title_text
        dialog.edit_dialog_name(st.session_state.name, st.session_state.selected_title, new_title)
        st.session_state.seleted_title = new_title
    if st.button('✏️', help='修改对话名称'):
        new_title = st.sidebar.text_input('修改名称', st.session_state.selected_title, help='修改当前对话标题', key='new_title_text', on_change=update_title)
        
        
from streamlit_extras.add_vertical_space import add_vertical_space
from tools import components
# buy me a coffee
with st.sidebar:
    components.display_sentry()
    # button(username="derekz", floating=False, width=221)

